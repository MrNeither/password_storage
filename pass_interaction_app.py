import json
import random
import string

from AES import AES


class PassStorage:
    __slots__ = ["key_path", "all_passwords", "aes", "commands", "running_commands"]

    def __init__(self):
        self.aes = None
        self.commands = None
        self.all_passwords = None
        self.key_path = None
        self.running_commands = None

    def init_after_install(self):
        key_path = input("input path to file with key >> ")
        if self.check_key_path(key_path):
            self.key_path = key_path
        else:
            raise ValueError

        self.aes = AES()
        self.aes.key = self.get_key()
        self.commands = {
            "q": ("quit", self.quit),
            "ls": ("list all services", self.list_all),
            "a": ("add a record", self.add),
            "d": ("delete a record", self.delete),
            "ed": ("edit a record", self.edit),
            "h": ("show help", self.help),
            "gp": ("get pass by service", self.show_one),
            "gk": ("gen key (will be in 'key.txt')", self.gen_aes_key)
        }
        self.all_passwords = self.decrypt_all()
        self.running_commands = True

    def decrypt_all(self):
        with open("passwords.txt", "r") as file:
            encrypted_passwords = file.read()
        if encrypted_passwords == "":
            print("file with passwords is empty")
            return dict()

        encrypted_codes = self.get_list_of_nums(encrypted_passwords)
        self.aes.open_bytes = encrypted_codes[:]
        self.aes.cipher_bytes = encrypted_codes[:]
        open_codes = self.aes.decrypt()
        open_pass = self.__get_text_from_list_of_nums(open_codes)
        return json.loads(open_pass)

    @staticmethod
    def get_list_of_nums(nums_in_row):
        cymb_per_num = int(nums_in_row[0], 10)
        list_of_nums = [int(nums_in_row[((i-1)*cymb_per_num + 1):(i*cymb_per_num+1)], 10)
                        for i in range(1, 1+(len(nums_in_row)-1)//cymb_per_num)]
        return list_of_nums

    def show_one(self):
        service = self.input_service()
        for num, acc in enumerate(self.all_passwords[service]):
            print(f"{num}--username = {acc['username']}   |   password={acc['password']}")
        show_full = input("input num of acc to show full info(or 'e' to exit) \n>> ")
        if show_full != 'e':
            show_full, good_res = self.input_num_of_acc(show_full, service)
            if good_res:
                self.print_account(self.all_passwords[service][show_full])

        print("finish show_one")

    def help(self):
        for k, v in self.commands.items():
            print(f" {k} - {v[0]}")

    def list_all(self):
        for num, service in enumerate(self.all_passwords.keys()):
            print(f"{num}-- {service}")

    def add(self):
        cur_service = input("input service >> ")
        self.all_passwords.setdefault(cur_service, [])
        self.add_account(cur_service)
        print("finish adding")

    def add_account(self, service):
        username = input("input username >> ")
        password = input("input password >> ")
        new_account = {
            "username": username,
            "password": password
        }
        add_field = input("add a field[y/n] >> ")
        while add_field == "y":
            field = input("input a field name >> ")
            f_value = input("input a field value >> ")
            new_account[field] = f_value
            add_field = input("add a field[y/n] >> ")

        self.all_passwords[service].append(new_account)

    def input_service(self):
        while True:
            service = input("input service >> ")
            if service in self.all_passwords.keys():
                break
            print("wrong service name")
            self.list_all()
        return service

    def input_num_of_acc(self, num_to_delete, service) -> (int, bool):
        try:
            num_to_delete = int(num_to_delete, 10)
            if len(self.all_passwords[service]) < num_to_delete and num_to_delete >= 0:
                return num_to_delete, True
            else:
                print(f"num not in ranges [0 <= num < {len(self.all_passwords[service])}]")
        except Exception:
            print("wrong num format (not int)")
        return None, False

    def delete(self):
        service = self.input_service()
        ans = input("delete the whole service? [y/n]")
        if ans == "y":
            del self.all_passwords[service]
        else:
            self.print_all_accounts(service)
            num_to_delete = input("input the number of account to delete ['s' to stop] \n>> ")
            while num_to_delete != "s":
                num_to_delete, good_res = self.input_num_of_acc(num_to_delete, service)
                if good_res:
                    del self.all_passwords[service][num_to_delete]
                self.print_all_accounts(service)
                num_to_delete = input("input the number of account to delete ['s' to stop] \n>> ")
        print("finish deleting")

    def print_all_accounts(self, service):
        for num, account in self.all_passwords[service]:
            self.print_account(account, num)

    def print_account(self, account, num_of_acc_to_print=None):
        if num_of_acc_to_print is not None:
            print(f"----------\n account num = {num_of_acc_to_print}")
        for k, v in account.items():
            print(f"{k} = {v}")

    def edit(self):
        service = self.input_service()
        self.print_all_accounts(service)
        num_to_edit = input("input the number of account to edit ['s' to stop] \n>> ")
        while num_to_edit != "s":
            num_to_edit, good_res = self.input_num_of_acc(num_to_edit, service)
            if good_res:
                self.edit_acc(service, num_to_edit)
            num_to_edit = input("input the number of account to edit ['s' to stop] \n>> ")
        print("finish editing")

    def edit_acc(self, service, num_of_acc):
        for key in self.all_passwords[service][num_of_acc].keys():
            print(key)

        while True:
            field = input("input field to edit ['s' to stop] \n>> ")
            if field == 's':
                break
            if field not in self.all_passwords[service][num_of_acc].keys():
                print("There is no such field")
                continue

            f_value = input("input new field value >> ")
            self.all_passwords[service][num_of_acc][field] = f_value

    def save(self):
        pack_passwords = json.dumps(self.all_passwords)
        self.aes.prepare_text(pack_passwords)
        encr_passwords = self.aes.encrypt()

        encr_text = self.get_encr_text(encr_passwords)

        with open("passwords.txt", "w") as file:
            file.write(encr_text)

    def get_encr_text(self, encr_pass):
        encr_pass = [str(i) for i in encr_pass]
        max_len = len(max(encr_pass, key=len))
        if len(str(max_len)) > 1:
            print("error. too long numbers. mass will be stored in the file")
            return str(encr_pass)
        encr_text = str(max_len)
        for num in encr_pass:
            encr_text += self.get_str_from_num(max_len, num)
        return encr_text

    @staticmethod
    def get_str_from_num(max_len, num):
        return "0"*(max_len - len(str(num))) + str(num)

    @staticmethod
    def __get_text_from_list_of_nums(l: list):
        text_after = ''.join([chr(num) for num in l if num != 0])
        return text_after

    @staticmethod
    def check_key_path(key_path):
        result = True
        if type(key_path) is not str:
            print(f"key_path type is not str. It is {type(key_path)}")
            result = False
        return result

    def quit(self):
        saves = input("Save? y/[something else]")
        if saves == 'y':
            print("Saving...")
            self.save()
        self.running_commands = False

    def get_key(self):
        with open(self.key_path, "r") as file:
            text_key = file.read()
        return text_key

    @staticmethod
    def gen_aes_key(key_len=128):
        text_key = [random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
                    for _ in range(key_len // 8)]
        symb_codes = [str(ord(symb)) for symb in text_key]
        symb_codes = ["0" * (3 - len(code)) + code for code in symb_codes]
        symb_codes = ''.join(symb_codes)

        with open('key.txt', 'w') as file:
            file.write(symb_codes)
        print("key is written into 'key.txt'")

    def run(self):
        self.init_after_install()
        print("input 'h' to print all commands")
        while self.running_commands:
            input_comand = input(">> ")
            if input_comand in self.commands.keys():
                self.commands[input_comand][1]()
            else:
                print("wrong command")
        print("finishing pass storage")

    def install(self):
        self.gen_aes_key()
        file = open("passwords.txt", "w")
        file.close()


if __name__ == "__main__":
    # aes = AES()
    # with open("key.txt", 'r') as file:
    #     aes.key = file.read()
    # open_txt = "some text"
    # aes.prepare_text(open_txt)
    # enc_txt = aes.encrypt()
    # text_after = ''.join([chr(num) for num in enc_txt if num != 0])


    p = PassStorage()
    p.run()
