# Logging Setup with AttributeLogger

## 1. Logger Configuration in `settings.py`

In your `settings.py` file, configure the logger using the `LOGGING` setting:
# settings.py ([LOGGING](./logger.py#L11))

## 2. Custom Formatters and Handlers ([LOGGING](./logger.py#L84))

## 3. Custom counter logger and Handlers ([LOGGING](./logger.py#L151))

## `AttributeLogger` Class Methods ([AttributeLogger](./logger.py#L216))

### `info(self, msg: str, *args, **kwargs)` ([AttributeLogger](./logger.py#L255))
- **Purpose:** Log an info message with additional attributes.
- **Arguments:**
  - `msg (str)`: The log message.
  - `*args`: Variable length argument list.
  - `**kwargs`: Keyword arguments for additional configuration.

### `error(self, msg: str, *args, **kwargs)` ([AttributeLogger](./logger.py#L268))
- **Purpose:** Log an error message with additional attributes.
- **Arguments:**
  - `msg (str)`: The log message.
  - `*args`: Variable length argument list.
  - `**kwargs`: Keyword arguments for additional configuration.

### `debug(self, msg: str, *args, **kwargs)` ([AttributeLogger](./logger.py#L281))
- **Purpose:** Log a debug message with additional attributes.
- **Arguments:**
  - `msg (str)`: The log message.
  - `*args`: Variable length argument list.
  - `**kwargs`: Keyword arguments for additional configuration.

### `warning(self, msg: str, *args, **kwargs)` ([AttributeLogger](./logger.py#L294))
- **Purpose:** Log a warning message with additional attributes.
- **Arguments:**
  - `msg (str)`: The log message.
  - `*args`: Variable length argument list.
  - `**kwargs`: Keyword arguments for additional configuration.

### `fatal(self, msg: str, *args, **kwargs)` ([AttributeLogger](./logger.py#L307))
- **Purpose:** Log a fatal message with additional attributes.
- **Arguments:**
  - `msg (str)`: The log message.
  - `*args`: Variable length argument list.
  - `**kwargs`: Keyword arguments for additional configuration.

### `with_attributes(self, **kwargs)` ([AttributeLogger](./logger.py#L320))
- **Purpose:** Create a new `AttributeLogger` with additional attributes.
- **Arguments:**
  - `**kwargs`: Additional attributes to be added.
- **Returns:** A new instance of `AttributeLogger` with the updated attributes.



### use of the AttributeLogger - ([AttributeLogger](./logger.py#L337))