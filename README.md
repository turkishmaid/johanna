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

## Minimal Example

```python
import johanna

def main():
    johanna.apply_schema("./schema.sql")
    with johanna.Connection("Charlotte") as c:
        c.cur.execute("insert or ignore into kvpairs(k, v) values (1, 'eins')")
        c.commit()

if __name__ == "__main__":
    johanna.main(main)
```
