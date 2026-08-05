mod benchmark;
mod data_gen;
mod instance;
pub mod caramel;

#[test]
pub fn foo() {
    let car = caramel::CsfU32::new(&[b"foo".as_slice()], &[22]).unwrap();
    println!("{:?}", car.query(*&b"foo"));
    
    panic!()
}
