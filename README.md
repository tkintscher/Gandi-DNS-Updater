This script updates the A or AAAA records of a subdomain
managed by [Gandi](https://gandi.net).

It has no external requirements besides Python 3.
This facilitates deployment on lightweight systems such as NAS, Raspberry Pi, etc.
and running via schedulers (e.g. systemd-timers or cron).

The external IP address can be determined automatically through
the service provided by [ifconfig.co](https://ifconfig.co).
Please respect its rate limit policy:
> *Please limit automated requests to 1 request per minute.*
> No guarantee is made for requests that exceed this limit.
> They may be rate-limited, with a 429 status code, or dropped entirely.


## Requirements

  * Python 3

## Usage

```bash
usage: gandi.py [-h] GANDI_API_KEY subdomain.domain.tld {A,AAAA} [address]
```

  * `GANDI_API_KEY` is the API key that can be obtained
    from the administration interface for the domain on the Gandi website.
  * Use `A` to update the IPv4 record, and `AAAA` to update the IPv6 record.
  * As for the target address to set, there are three options:

### Option A: Automatically determine external IP address

```bash
$ ./gandi.py GANDI_API_KEY foo.example.com AAAA
```

This method uses the service of [ifconfig.co](https://ifconfig.co) to determine
the external IP address of the current machine.
As mentioned before, please be responsible and do not use this service
more than once per minute.

### Option B: Use a fixed address

```bash
$ ./gandi.py GANDI_API_KEY foo.example.com AAAA ::1
```
Now the `AAAA` record of `foo.example.com` will point to `::1`.

### Option C: Use the address of another host

```bash
$ ./gandi.py GANDI_API_KEY foo.example.com AAAA foobox
```

The IP address of `foobox` will be resolved and
written to the `AAAA` record of `foo.example.com`.

This way one machine can update the records of several other hosts,
e.g. on the local network.
Note that this may not make much sense if `foobox` is resolved to
a local (IPv4) address as is the case behind NAT.

## Use with systemd timers

Regular updates of the domain records can be performed using
`systemd` timers:

  * Edit `gandi-update.sh` to your needs.
  * In `gandi-update.service` change the `WorkingDirectory` path to the checkout directory.
  * Link the files to systemd's config:
    ```bash
    mkdir -p $HOME/.config/systemd/user
    ln -s $PWD/gandi-update.{service,timer} $HOME/.config/systemd/user
    ```
  * Enable the timer:
    ```bash
    systemctl --user enable gandi-update.timer
    ```
