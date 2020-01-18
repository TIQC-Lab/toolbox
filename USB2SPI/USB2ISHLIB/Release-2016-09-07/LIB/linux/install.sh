
TARGET="libUSB2UIS.so.1.0.0"
TARGETA="libUSB2UIS.a"
TARGETD="libUSB2UIS.so.1.0.0"
TARGET0="libUSB2UIS.so"
TARGET1="libUSB2UIS.so.1"
TARGET2="libUSB2UIS.so.1.0"


	test -d /usr/local/lib || mkdir -p /usr/local/lib
	install -m 755 -p libUSB2UIS.so.1.0.0 /usr/local/lib/libUSB2UIS.so.1.0.0
	strip --strip-unneeded /usr/local/lib/libUSB2UIS.so.1.0.0
	ln -f -s libUSB2UIS.so.1.0.0 /usr/local/lib/libUSB2UIS.so
	ln -f -s libUSB2UIS.so.1.0.0 /usr/local/lib/libUSB2UIS.so.1
	ln -f -s libUSB2UIS.so.1.0.0 /usr/local/lib/libUSB2UIS.so.1.0


