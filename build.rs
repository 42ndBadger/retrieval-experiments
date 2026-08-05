fn main() {
    let dst = cmake::Config::new("caramel").profile("Release").build();
    println!(
        "cargo:rustc-link-search=native={}",
        dst.join("lib").display()
    );
    println!("cargo:rustc-link-lib=static=caramel_lib");
    println!("cargo:rustc-link-lib=stdc++");
    println!("cargo:rustc-link-lib=gomp");
    println!("cargo:rustc-link-lib=m");
}
