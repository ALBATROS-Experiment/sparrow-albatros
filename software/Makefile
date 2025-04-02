# Default rule
all: dump_baseband

dump_baseband: dump_baseband.c
	gcc -o dump_baseband dump_baseband.c inih/ini.c -lpcap 

clean:
	rm -f dump_baseband
