# Default rule
all: dump_baseband

dump_baseband: dump_baseband.c lbtools.c
	gcc -o dump_baseband dump_baseband.c lbtools.c inih/ini.c -lpcap -lusb-1.0

clean:
	rm -f dump_baseband
