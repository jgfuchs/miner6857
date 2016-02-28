extern crate crypto;
extern crate rand;
extern crate rustc_serialize;
extern crate time;
extern crate byteorder;

use std::env;
use std::collections::HashMap;

use rustc_serialize::hex::*;
use crypto::digest::Digest;
use crypto::sha2::Sha256;
use byteorder::{BigEndian, ByteOrder};

// Hardcoded constants:
//      d = 42, N = 2^d = 2^42
//      alpha = 1/3
//      beta = 2/3
//      gamma = (1 - alpha)/2 = 1/3

// x & MASK_42 == x % 2^42
const MASK_42: u64 = 0x3ffffffffff;

// all exponents: real value = 2^x
const N: u64 = 32;
const NA: u64 = N / 3;
const NB: u64 = N * 2 / 3;
const NC: u64 = N / 3;

fn main() {
    if env::args().count() != 2 {
        println!("miner <hex encoded template data>\n");
        return;
    }

    let data = env::args().last().unwrap().from_hex().unwrap();
    assert!(data.len() == 89);

    println!("Difficulty = {}, α = {}, β = {}, γ = {}", N, NA, NB, NC);

    let two_colls = find_2_collisions(&data);
    println!("{:?}", two_colls);
}

fn find_2_collisions(templ: &Vec<u8>) -> HashMap<u64, (u64, u64)> {
    let na = 1 << NA;
    let nc = 1 << NC;

    // scratch space for calc_hash()
    let scratch: &mut [u8] = &mut templ.clone();

    // maps (chain end point) -> (chain start point)
    let mut chains = HashMap::new();
    chains.reserve(na);

    // find 2^a chains of length 2^c each
    for _ in 0..na {
        let a0 = rand::random::<u64>() & MASK_42;
        let mut a = a0;
        for _ in 0..nc {
            a = calc_hash(scratch, a);
        }
        chains.insert(a, a0);
    }

    // map (hash value) -> (1st preimage, 2nd preimage)
    let preimg = HashMap::new();

    let mut nfound = 0;
    while nfound < 10 {
        let a = rand::random::<u64>() & MASK_42;
        let mut b = a;
        for _ in 0..nc {
            b = calc_hash(scratch, b);

        }
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

    BigEndian::read_u64(&out[24..]) & MASK_42
}
