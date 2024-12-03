# LazyExceptions Class - Lazy Loading of Exceptions

## Description

The code snippet is part of a module that provides lazy loading of exceptions from a specified module. It defines a class called `LazyExceptions` that contains two methods: `get_all_classes` and `lazy_exceptions`.

## Inputs

The code snippet relies on the existence of the `utils.django.exceptions` module and its classes. It does not have explicit inputs.

## Flow

1. The `get_all_classes` method takes a module name as input and imports the specified module using `importlib.import_module`.
2. It uses the `inspect.getmembers` function to retrieve all the members (classes, functions, etc.) of the imported module.
3. Classes are filtered out using `inspect.isclass`, and a tuple of class objects is returned.

4. The `lazy_exceptions` method creates a lazy object for each class in the `utils.django.exceptions` module using `SimpleLazyObject` and a lambda function.
5. It returns a tuple of these lazy objects.

## Outputs

The code snippet does not have explicit outputs. However, it provides a way to lazily load the classes from the `utils.django.exceptions` module.

## Usage Example

```python
# Create an instance of the LazyExceptions class
lazy_exceptions = LazyExceptions().lazy_exceptions

# Iterate over lazy_exceptions and print each one
for lazy_exception in lazy_exceptions:
    print(lazy_exception)
```