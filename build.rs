use std::env;
use std::path::Path;

fn main() {
    // Without an explicit out_dir, `cmake::Config::build()` defaults to
    // `<OUT_DIR>/build` for *every* call in this build script - so a
    // second `cmake::Config::new(...)` call would reuse (and reconfigure)
    // the exact same directory the first one just built in, silently
    // colliding two unrelated CMake projects. Give each its own subtree.
    let out_dir = env::var("OUT_DIR").expect("OUT_DIR set by cargo");

    let caramel_dst = cmake::Config::new("caramel")
        .profile("Release")
        .out_dir(Path::new(&out_dir).join("caramel"))
        .build();
    println!(
        "cargo:rustc-link-search=native={}",
        caramel_dst.join("lib").display()
    );
    println!("cargo:rustc-link-lib=static=caramel_lib");

    let lsf_dst = cmake::Config::new("lsf")
        .profile("Release")
        .out_dir(Path::new(&out_dir).join("lsf"))
        .define("CMAKE_POLICY_VERSION_MINIMUM", "3.5")
        .build();
    println!(
        "cargo:rustc-link-search=native={}",
        lsf_dst.join("lib").display()
    );
    println!("cargo:rustc-link-lib=static=lsf_shim");
    println!("cargo:rustc-link-lib=static=tlx");

    println!("cargo:rustc-link-lib=stdc++");
    println!("cargo:rustc-link-lib=gomp");
    println!("cargo:rustc-link-lib=m");
    println!("cargo:rustc-link-lib=pthread");
}
