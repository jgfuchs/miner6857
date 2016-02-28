extern crate openssl;
extern crate sodiumoxide;
extern crate crypto;
extern crate time;

use openssl::crypto::hash::{Type, hash};

use sodiumoxide::crypto::hash::sha256;
use sodiumoxide::randombytes::randombytes_into;

use crypto::digest::Digest;
use crypto::sha2::Sha256;

use std::io::Write;

fn sink(data: &[u8]) {
    writeln!(&mut std::io::stderr(), "{}", data.len());
}

fn test_openssl(data: &[u8]) {
    let h = hash(Type::SHA256, data);
    sink(&h);
}

fn test_sodiumoxide(data: &[u8]) {
    let h = sha256::hash(data);
    sink(h.as_ref());
}

fn test_crypto(data: &[u8]) {
    let mut s = Sha256::new();
    s.input(data);
    let mut out = [0u8; 256/8];
    s.result(&mut out);
    sink(&out);
}

fn main() {
    sodiumoxide::init();

    let fns: [fn(&[u8]); 3] = [test_openssl, test_sodiumoxide, test_crypto];
    let mut times = [0u64; 3];

    const IT: u32 = 1_000_000;

    let mut data = [0u8; 128];

    for i in 0..3 {
        fns[i](&data);
    }

    for _ in 0..IT {
        randombytes_into(&mut data);
        for i in 0..3 {
            let start = time::precise_time_ns();
            fns[i](&data);
            times[i] += time::precise_time_ns() - start;
        }
    }

    for i in 0..3 {
        println!("{:.0} ns/hash", times[i] as f32 / IT as f32);
    }
}
