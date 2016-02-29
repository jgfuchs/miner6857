extern crate byteorder;
extern crate crypto;
extern crate rand;
extern crate rustc_serialize;
extern crate time;

use std::collections::HashMap;
use std::env;
use std::io::Write;
use std::sync::{mpsc, Arc};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;

use byteorder::{BigEndian, ByteOrder};
use crypto::digest::Digest;
use crypto::sha2::Sha256;
use rustc_serialize::hex::*;

macro_rules! println_stderr(
    ($($arg:tt)*) => (
        match writeln!(&mut ::std::io::stderr(), $($arg)* ) {
            Ok(_) => {},
            Err(x) => panic!("Unable to write to stderr: {}", x),
        }
    )
);

// Hardcoded constants:
//      d = 42, N = 2^d = 2^42
//      alpha = 1/3
//      beta = 2/3
//      gamma = (1 - alpha)/2 = 1/3

// all exponents: real value = 2^x
const D: u64 = 44;
const A: u64 = D / 3;
const B: u64 = D * 2 / 3;
const C: u64 = D / 3;

// x & MOD_MASK == x % 2^d
const MOD_MASK: u64 = (1 << D) - 1;

const NTHREADS_1: usize = 2;
const NTHREADS_2: usize = 4;

fn main() {
    if env::args().count() != 2 {
        println_stderr!("miner <hex encoded template data>\n");
        return;
    }

    let data = env::args().last().unwrap().from_hex().unwrap();
    assert!(data.len() == 89);

    println_stderr!("Difficulty = {}, α = {}, β = {}, γ = {}", D, A, B, C);

    find_2_collisions(&data);
}

fn find_2_collisions(templ: &Vec<u8>) -> HashMap<u64, (u64, u64)> {
    let na = 1 << A;
    let nc = 1 << C;

    println_stderr!("Creating {} {}-chains...", na, nc);
    let start = time::precise_time_s();
    let chains = make_chains(na, nc, &templ);
    let end = time::precise_time_s();
    println_stderr!("\tdone (time: {:.4} s)", end - start);

    println_stderr!("Looking for 2-collisions...");
    let start = time::precise_time_s();
    let preimg = collide_chains(chains, na, nc, &templ);
    let end = time::precise_time_s();
    println_stderr!("\tdone, found {} (time: {:.4} s)", preimg.len(), end - start);

    preimg
}

fn make_chains(na: usize, nc: usize, data: &Vec<u8>) -> HashMap<u64, u64> {
    let mut chains = HashMap::new();
    chains.reserve(na);

    let (tx, rx) = mpsc::channel();
    let mut threads = Vec::new();

    for _ in 0..NTHREADS_1 {
        let tx = tx.clone();
        let data = data.clone();

        let t = thread::spawn(move || {
            let scratch: &mut [u8] = &mut (data.clone());
            for _ in 0..(na / NTHREADS_1) {
                let start = rand_nonce();
                let mut a = start;
                for _ in 0..nc {
                    a = calc_hash(scratch, a);
                }
                tx.send((a, start)).unwrap();
            }
            drop(tx);
        });

        threads.push(t);
    }

    drop(tx);

    for (end, start) in rx.iter() {
        chains.insert(end, start);
    }

    for t in threads {
        t.join().unwrap();
    }

    chains
}

fn collide_chains(chains: HashMap<u64, u64>, na: usize, nc: usize, data: &Vec<u8>) -> HashMap<u64, (u64,  u64)> {
    let chains = Arc::new(chains);
    let nfound = Arc::new(AtomicUsize::new(0));

    let (tx, rx) = mpsc::channel();
    let mut threads = Vec::new();

    for _ in 0..NTHREADS_2 {
        let chains = chains.clone();
        let data = data.clone();
        let tx = tx.clone();
        let nfound = nfound.clone();

        let t = thread::spawn(move || {
            loop {
                if nfound.load(Ordering::SeqCst) >= na {
                    break;
                }

                let scratch: &mut [u8] = &mut data.clone();

                let mut a = rand_nonce();
                let mut b = a;
                for j in 0..nc {
                    b = calc_hash(scratch, b);
                    if chains.contains_key(&b) {
                        let mut ap = chains[&b];
                        for _ in 0..(nc - j - 1) {
                            ap = calc_hash(scratch, ap);
                        }
                        if a != ap {
                            b = calc_hash(scratch, a);
                            let mut bp = calc_hash(scratch, ap);

                            while b != bp {
                                a = b;
                                ap = bp;
                                b = calc_hash(scratch, a);
                                bp = calc_hash(scratch, ap);
                            }

                            tx.send((b, (a, ap))).unwrap();
                        }
                        break;
                    }
                }
            }
        });

        threads.push(t);
    }

    drop(tx);

    let mut preimg = HashMap::new();
    for (img, (pre1, pre2)) in rx.iter() {
        if preimg.contains_key(&img) {
            let (p1, p2) = preimg[&img];
            if (p1, p2) == (pre1, pre2) || (p2, p1) == (pre1, pre2) {
                continue;
            } else {
                if p1 != pre1 && p1 != pre2 {
                    println!("{} {} {}", pre1, pre2, p1);
                }
                if p2 != pre1 && p2 != pre2 {
                    println!("{} {} {}", pre1, pre2, p2);
                }
                std::process::exit(0);
            }
        }

        preimg.insert(img, (pre1, pre2));

        let n = nfound.fetch_add(1, Ordering::SeqCst);
        if n & 0xFF == 0 {
            println_stderr!("\t{}", n);
        }
    }

    for t in threads {
        t.join().unwrap();
    }

    preimg
}

// inserts the nonce into the data template, and
// returns the SHA256 hash of that (mod 2^42)
fn calc_hash(buf: &mut [u8], nonce: u64) -> u64 {
    assert!(buf.len() == 89);

    BigEndian::write_u64(&mut buf[80..88], nonce);

    let mut hasher = Sha256::new();
    hasher.input(buf);
    let mut out = [0u8; 32];
    hasher.result(&mut out);

    BigEndian::read_u64(&out[24..]) & MOD_MASK
}

fn rand_nonce() -> u64 {
    rand::random::<u64>() & MOD_MASK
}
