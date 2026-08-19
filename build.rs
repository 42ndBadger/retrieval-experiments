fn main() {
    let caramel_dst = cmake::Config::new("caramel").profile("Release").build();
    println!(
        "cargo:rustc-link-search=native={}",
        caramel_dst.join("lib").display()
    );
    println!("cargo:rustc-link-lib=static=caramel_lib");

    let lsf_dst = cmake::Config::new("lsf").profile("Release").build();
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
