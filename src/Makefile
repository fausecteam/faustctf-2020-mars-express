CC = gcc
MCC ?= movcc
CFLAGS = -no-pie -m32 -Wextra -Werror=extra -Wno-long-long -Wno-variadic-macros -fexceptions
MCFLAGS = -Wf--crtd -Wf--no-mov-flow -Wf--no-mov-loop
LIBFLAGS = -lncurses

CDIR = src
MCDIR = src/mov
INCDIR = src/include
OUTDIR = build

SOURCES = $(wildcard $(CDIR)/*.c)
MSOURCES = $(wildcard $(MCDIR)/*.c)

WRAPPER = helper/wrapper.s
PATCHFILE = helper/movfuscated.patch

MASSEMBLYS = $(MSOURCES:$(MCDIR)/%.c=$(OUTDIR)/%.s)
OBJS = $(SOURCES:$(CDIR)/%.c=$(OUTDIR)/%.o)

TARGET = mars-express

.PHONY:
all: $(TARGET)

$(OUTDIR):
	mkdir -p $(OUTDIR)

$(OUTDIR)/%.s: $(MCDIR)/%.c $(OUTDIR)
	$(MCC) $(MCFLAGS) -S -o $@ $^
	patch $@ --no-backup-if-mismatch -i $(PATCHFILE)

$(OUTDIR)/%.o: $(CDIR)/%.c $(OUTDIR)
	$(CC) $(CFLAGS) -I $(INCDIR) -c -o $@ $<

$(TARGET): $(OBJS) $(MASSEMBLYS) $(WRAPPER)
	$(CC) $(CFLAGS) -I $(INCDIR) -o $(TARGET) $^ $(LIBFLAGS)
	strip $(TARGET)

.PHONY:
clean:
	rm -rf $(MASSEMBLYS) $(OBJS) $(OUTDIR)

.PHONY:
dist-clean: clean
	rm -f $(TARGET)

