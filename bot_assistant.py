from collections import UserDict
from datetime import date, datetime, timedelta
import pickle


class ValidationError(Exception):
    pass

class NotFoundError(Exception):
    pass

class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value: str):
        if not value:
            raise ValidationError("Name cannot be empty")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value: str):
        super().__init__(value)

    def validate_phone(self, phone: str):
        return isinstance(phone, str) and len(phone) == 10 and phone.isdigit()
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value: str):
        if not self.validate_phone(new_value):
            raise ValidationError("Invalid phone number format")
        self._value = new_value
    
class Birthday(Field):
    def __init__(self, value: str):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValidationError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = self.birthday.value if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {birthday_str}"

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise NotFoundError("Phone number not found")

    def edit_phone(self, old_phone: str, new_phone: str):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise NotFoundError("Phone number not found")

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str):
        if name not in self.data:
            raise NotFoundError("Contact not found")
        del self.data[name]

    def get_upcoming_birthdays(self) -> list:
        format_date = "%d.%m.%Y"
        congratulation_users = []
        current_date = date.today()

        for record in self.data.values():
            if record.birthday is None:
                continue

            target_date = datetime.strptime(record.birthday.value, format_date).date()
            target_date_norm = target_date.replace(year=current_date.year)

            if target_date_norm < current_date:
                target_date_norm = target_date_norm.replace(year=current_date.year + 1)

            days_to_birthday = (target_date_norm - current_date).days

            if days_to_birthday <= 7:
                congratulation_date = target_date_norm
                if congratulation_date.weekday() >= 5:
                    days_to_add = 7 - congratulation_date.weekday()
                    congratulation_date += timedelta(days=days_to_add)

                congratulation_users.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })

        return congratulation_users


def parse_input(user_input: str) -> tuple:
    parts = user_input.split()

    if not parts:
        return "", []
    
    cmd, *args = parts
    return cmd.strip().lower(), args

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return str(e)
        except NotFoundError as e:
            return str(e)
        except (ValueError, IndexError):
            return "Invalid command format."
    return inner

@input_error
def add_contact(args, book: AddressBook) -> str:
    name, phone = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        book.add_record(record)

    record.add_phone(phone)
    
    return "Contact added."

@input_error
def change_contact(args, book: AddressBook) -> str:
    name, phone = args
    record: Record = book.find(name)

    if record is None:
        raise NotFoundError("Contact not found")

    if record.phones:
        record.edit_phone(record.phones[0].value, phone)
    else:
        record.add_phone(phone)

    return "Contact updated."

@input_error
def show_phone(args, book: AddressBook) -> str:
    name = args[0]
    record: Record = book.find(name)

    if record is None:
        raise NotFoundError("Contact not found")

    return f"{record.name.value}: {'; '.join(p.value for p in record.phones)}"

@input_error
def show_all(book: AddressBook) -> str:
    if not book.data:
        return "No contacts found."

    return "\n".join(f"{record.name.value}: {'; '.join(p.value for p in record.phones)}" for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook) -> str:
    name, birthday = args
    record: Record = book.find(name)

    if record is None:
        raise NotFoundError("Contact not found")

    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook) -> str:
    name = args[0]
    record: Record = book.find(name)

    if record is None:
        raise NotFoundError("Contact not found")

    if record.birthday is None:
        raise NotFoundError("Birthday not found")

    return record.birthday.value

@input_error
def birthdays(_, book: AddressBook) -> str:
    upcoming_birthdays = book.get_upcoming_birthdays()

    if not upcoming_birthdays:
        return "No upcoming birthdays found."

    return "\n".join(f"{user['name']} - {user['congratulation_date']}" for user in upcoming_birthdays)

def exit_command(_):
    print("Good bye!")
    raise SystemExit

def save_data(book: AddressBook):
    with open("addressbook.pkl", "wb") as f:
        pickle.dump(book, f)

def load_data():
    try:
        with open("addressbook.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

def main():
    book = load_data()
    command_list = {
        "hello": lambda args: "How can I help you?",
        "add": lambda args: add_contact(args, book),
        "change": lambda args: change_contact(args, book),
        "phone": lambda args: show_phone(args, book),
        "all": lambda args: show_all(book),
        "add-birthday": lambda args: add_birthday(args, book),
        "show-birthday": lambda args: show_birthday(args, book),
        "birthdays": lambda args: birthdays(args, book),
        "exit": lambda args: (save_data(book), exit_command(args)),
        "close": lambda args: (save_data(book), exit_command(args))
    }

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        handler = command_list.get(command)

        if handler:
            print(handler(args))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
