# GM P59 — VPW Protocol Handler

Located at 0x0009BC in the Boot segment. Called on every diagnostic request from the OBD-II port.

## Mode Dispatcher

The factory OS dispatches VPW diagnostic modes with a chain of cmpi.b instructions:

```
0x0009BC: cmpi.b #$27, d0  -> Security Access
0x0009C2: cmpi.b #$28, d0  -> Communication Control
0x0009C8: cmpi.b #$34, d0  -> Download Request (flash write setup)
0x0009CE: cmpi.b #$36, d0  -> Data Transfer (flash write data)
0x0009D4: cmpi.b #$A0, d0  -> Custom diagnostic
0x0009DA: cmpi.b #$A1, d0  -> Custom diagnostic
```

## VPW Message Format

```
[priority] [dest_id] [source_id] [mode] [submode] [data...] [CRC]
   6C         10         F0        34      00       ...
```

## Standard Modes

| Mode | Direction | Purpose |
|------|-----------|---------|
| 0x20 | Tool to PCM | Halt kernel, reboot |
| 0x27 | Tool to PCM | Security Access (seed/key) |
| 0x34 | Tool to PCM | Request download |
| 0x35 | Tool to PCM | Request upload (read memory) |
| 0x36 | Tool to PCM | Transfer data (write to RAM/flash) |
| 0x3D | Tool to PCM | Kernel functions |

## Injection Point

The VPW handler at 0x00072A (called by the dispatcher at 0x000A1A) runs on every diagnostic request. This makes it an excellent hook point for injected code — any custom subroutine patched here will execute frequently.
