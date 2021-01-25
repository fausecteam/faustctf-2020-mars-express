mars express
============

Your friends in the outpost need special tools from the headquarters here on Mars!
Fortunatelly, you can send them by `mars-express`.
Get everything your friends need on the train and send it off!

```
         _____________________________  _______________________________  _______________________________ 
    _,-'/| #### | |          ####     ||                               ||                               |
 _-'            | |                   ||                               ||                               |
(------------------mars-express-------||-------------------------------||-------------------------------|
 \----(o)~~~~(o)----------(o)~~~~(o)--'`---(o)~~~(o)-------(o)~~~(o)---'`---(o)~~~(o)-------(o)~~~(o)---'
```

### General
A simple key/value store for creating trains and showing previous created trains.
The name of the train is the key, its contents are the values

### Build
You need `movcc` (see [movfuscator](https://github.com/xoreaxeaxeax/movfuscator.git)):
```bash
$ ./build_movcc.sh
```

Build:
```bash
$ make
```

Useful environment variables: `TERM=ansi77 COLUMNS=40 ROWS=20`.

### Vulnerability
There is a vulnerability in the heap implementation.
For every call to `malloc(size)`, the `size` is aligned to 2 bytes.
This alignment is intentionally implemented in a wrong way such that odd sizes are rounded down by one to the next even number.
Thus, this allows a one-byte overflow into the heap struct.
The attacker can leverage the one-byte overflow to gain arbitrary write.
By overwriting the `.got` and placing shellcode in the heap memory (`rwx` mapped), the attacker can start a shell.

You can find a sample exploit in [`exploit/x.py`](./exploit/x.py).

There is a directory traversal vulnerability in the train name.
The directory traversal itself is not exploitable.
Teams should realize that quickly.
Anyway, an unintended vulnerability is a simple buffer overflow when trying to access a previous train.
