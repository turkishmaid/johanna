# johanna

A sweet tiny app framework for Jenkins driven background apps.

This will support scheduled backgound tasks, typically started 
fron cron or Jenkins, by super simple 
- setup of a dot-folder in the user's `$HOME` or use the folder named in `$JOHANNA` 
- `.ini`-file based configuration
- logging support
- runtime and memory profiling
- SQLite connection handling
- mailgun support (needs credentials in the `.ini` file)

## Kickstart Background Procedure

```python
import johanna

def main():
    johanna.apply_schema("./schema.sql")
    with johanna.Connection("Charlotte") as c:
        c.cur.execute("insert or ignore into kvpairs(k, v) values (1, 'eins')")
        c.commit()

if __name__ == "__main__":
    johanna.main(main, mail_subject="Charlotte",
        dbname="charlotte.sqlite")
```

## Kickstart Interactive  Consumer

To consume data e.g. in Jupyter Notebooks, you will want less logging, no changes to the database, and no notification email. Please use "interactive mode" for such:

```python
import johanna

johanna.interactive(None, dbname="charlotte.sqlite")
with johanna.Connection("Charlotte") as c:
    c.cur.execute("select * from kvpairs")
    for row in c.cur:
        pass  # do something meaningful
```

_The synonym `johanna.interactive()` for `johanna.main(None,...)` has been added to make code more readable._

## Mailgun-Anschluss (optional)

Nachdem die Konfigurationsdatei `~/.dwd-cdc/dwd-cdc` angelegt ist, 
kann dort ein Abschnitt wie folgt manuell hinzugefügt werden:

```ini
[mailgun]
url = https://api.mailgun.net/v3/sandbox12345678901234567890123.mailgun.org/messages
auth-key = key-8674f976bb0w8678a0ds874sjldao787
from = dwd-cdc <postmaster@sandbox12345678901234567890123.mailgun.org>
to = Sara Ziner <do.not.use@example.com>
```

Wenn diese Konfiguration vorhanden ist, wird nach jedem Programmlauf die Print- und Log-Ausgabe über den
beschriebenen Mailgun-Account an die angegebene `to`-Adresse geschickt. Weitergehende Konfigurationsmöglichkeiten
werden (vielleicht) später hinzugefügt.

Ein kostenloser [mailgun](https://www.mailgun.com/) Account ("Flex Trial") ist für die Verwendung hier völlig
ausreichend. Man muss allerdings die Empfängeradressen vorher als "authorized recipients" anmelden 
und diese müssen es auch bestätigen.

