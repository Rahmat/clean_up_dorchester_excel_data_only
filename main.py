import pandas as pd

from collections import namedtuple
from dataclasses import dataclass

from prettyprinter import pprint as prettyprinter

# start of config
debugging = True

excel_file = "C:/Users/R1/Downloads/f.xls"

output_folder = "C:/Users/R1/Desktop/tmp/"
# end of config

combined_sheet_file = output_folder + "combined.csv"
cleaned_sheet_file = output_folder + "cleaned.csv"
output_filename = "test2.csv"
output_file = output_folder + output_filename

total_number_of_receipts = 0

organized_transactions = pd.DataFrame()

possible_discounts = []
possible_payment_methods = []


def data_after_first_char(data, char_to_split_on=":"):
    # splits on first char_to_split_on, and takes last of the results (second item and last item in the list)
    result = data.split(char_to_split_on, 1)[-1]
    # removes any " " chars, stops removing once it hits a non " " char.
    for char in result:
        if char != " ":
            break
        result = result[1:]
    return result


def col_num_to_string(n):
    # Full credit to https://stackoverflow.com/a/23862195/8333189
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def confirm_type(value, desired_type, row_num=None, col_num=None):
    try:
        desired_type(value)
    except ValueError:
        error_message = "'" + str(value) + "' could not be converted to a float!"
        if row_num and col_num:
            error_message += " See: " + col_num_to_string(col_num) + str(row_num)
        raise Exception(error_message)


def combine_sheets(input_file, output_file_name):
    input_workbook = pd.read_excel(input_file, sheet_name=None, ignore_index=True, header=None)

    combined_sheets_df = pd.concat(input_workbook.values())

    combined_sheets_df.to_csv(output_file_name, index=False, header=False)


def is_sorted(data_to_check):
    return data_to_check == sorted(data_to_check)


def get_receipt_rows(wb_rows: list):
    result = list()  # of named tuples
    ReceiptsRows = namedtuple('ReceiptsRows', ['start_row', 'end_row'])

    start_row: int = None
    for i, row_data in enumerate(wb_rows):
        # we're assuming the receipt has ended once we hit the next "Store"
        if row_data[0] != "Store :":
            continue

        if start_row is not None:
            end_row = i
            result.append(ReceiptsRows(start_row=start_row, end_row=end_row))

        # we're adding 1 to each row number because rows are 1 indexed
        start_row = i + 1
    result.append(ReceiptsRows(start_row=start_row, end_row=len(wb_rows)))

    return result


@dataclass
class VoidReceipts:
    rows_removed: int
    receipts_removed: int


def receipt_is_void(receipts_rows):
    for row_of_data in receipts_rows:
        if "All Void" in row_of_data[1]:
            return "True"


# noinspection PyUnboundLocalVariable
def clean_sheet(input_sheet, output_sheet,
                removing_blanks=True, removing_cashier_interrupts=True, removing_voids=False):
    my_wb = pd.read_csv(input_sheet, header=None, converters={i: str for i in range(100)})
    all_rows = list(my_wb.itertuples(index=False, name=None))
    print("starting length of my_wb:", len(my_wb))
    row_numbers_to_delete = []

    #  Remove blanks and cashier interrupts
    if removing_cashier_interrupts:
        cashier_interrupts_removed = 0
        cashier_interrupt_strings = ["Suspend by", "Resumed by"]
    if removing_blanks:
        blanks_removed = 0
    if removing_voids:
        voids_removed = VoidReceipts(rows_removed=0, receipts_removed=0)

    if removing_blanks:
        for i in range(100):
            if not any(all_rows[i]):
                if debugging:
                    print("Blank row detected at l" + str(i+1) + ". Row", str(i+1) + ":", all_rows[i])
                row_numbers_to_delete.append(i+1)
                blanks_removed += 1
            else:
                break
        else:  # no break
            raise Exception("Are there over 100 blank lines at the beginning of this file??")

    for receipts_rows in get_receipt_rows(wb_rows=all_rows):
        if removing_voids:
            if receipt_is_void(all_rows[receipts_rows.start_row-1:receipts_rows.end_row]):
                if debugging:
                    print("Deleting void transaction rows:", list(range(receipts_rows.start_row, receipts_rows.end_row + 1)))
                row_numbers_to_delete += list(range(receipts_rows.start_row, receipts_rows.end_row + 1))
                voids_removed.rows_removed += (receipts_rows.end_row + 1 - receipts_rows.start_row)
                voids_removed.receipts_removed += 1
                continue  # this receipt is no longer going to be kept, so no point checking it for other stuff?

        for row_num in range(receipts_rows.start_row, receipts_rows.end_row + 1):  # each row in receipts_rows
            row_of_data = all_rows[row_num-1]

            if removing_cashier_interrupts:
                second_column_cell_value = row_of_data[1]
                if any(disallowed_string in second_column_cell_value for disallowed_string in cashier_interrupt_strings):
                    if debugging:
                        print("Suspend or Resume detected at b" + str(row_num) + ". Row", str(row_num) + ":", row_of_data)
                    row_numbers_to_delete.append(row_num)
                    cashier_interrupts_removed += 1
                    continue

            if removing_blanks:
                #  'any()' checks if there's any empty strings in the list of data
                if not any(row_of_data):
                    if debugging:
                        print("Blank row detected at l" + str(row_num) + ". Row", str(row_num) + ":", row_of_data)
                    row_numbers_to_delete.append(row_num)
                    blanks_removed += 1

    print(row_numbers_to_delete)
    if not is_sorted(row_numbers_to_delete):
        raise Exception("row_numbers_to_delete was not sorted by default (implicitly). Sounds like something messed up")
    indexes_to_delete = [num-1 for num in row_numbers_to_delete]
    my_wb.drop(index=indexes_to_delete, inplace=True)

    if debugging:
        if removing_voids:
            print(voids_removed.receipts_removed, "void receipts removed (" + str(voids_removed.rows_removed) + " rows removed in total)")
        if removing_cashier_interrupts:
            print(cashier_interrupts_removed, "cashier interrupts removed")
        if removing_blanks:
            print(blanks_removed, "blanks removed")
        print(len(row_numbers_to_delete), "total deletes occurred!",
              len(row_numbers_to_delete), "+", len(my_wb), "=", len(row_numbers_to_delete) + len(my_wb))

    my_wb.to_csv(output_sheet, index=False, header=False)


'''RECEIPT LAYOUT
    Transaction info
    Headers
    
    Items
    
    Discounts
    
    Subtotal
    Payment payment_method
    Total
    FSP Eligibility (is what category?)
    Total tendered
    Change
    
    Card Info
    
    Amount
    Approval#
    Date (seems like a repeat of transaction end time)
'''


@dataclass
class CardInformation:
    card_holder_name: str  # doesnt seem to be there for ebt
    card_type: str  # Remove 'Card Type: '
    account_num: str  # Remove 'Account #: '
    exp_date: str  # Remove 'Exp Date : '

    amount: str
    approval_num: str
    current_date: str
    reference_num: str


'''
class Item:
    def __init__(self, item_id=None, receipt_alias=None, qty_sold=None, unit_price=None, ext_price=None):
        self.item_id: str = item_id
        self.receipt_alias: str = receipt_alias
        self.qty_sold: float = qty_sold
        self.unit_price: float = unit_price
        self.ext_price: float = ext_price

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
'''


@dataclass
class Item:
    item_id: str
    receipt_alias: str
    qty_sold: float
    unit_price: float
    ext_price: float


@dataclass
class Discount:
    receipt_alias: str
    ext_price: float


class Receipt:
    def __init__(self):
        self.position_in_excel: str = None

        self.store_name: str = None
        self.start_time: str = None
        self.end_time: str = None
        self.invoice_number: str = None
        self.terminal_number: str = None
        self.customer_number: str = None
        self.receipt_number: str = None
        self.customer_name: str = None
        self.cashier_name: str = None

        self.items: list = None  # List of Item()s. Started as None so that when entering into DB we just need to check if None.

        self.discounts: list = None  # Employee Discount

        # possible_payment_methods = ["Credit", "Debit", "Cash", "EBT", "Gift Card", "EBT Cash"]
        self.credit: float = None
        self.debit: float = None
        self.cash: float = None
        self.ebt: float = None
        self.gift_card: float = None
        self.ebt_cash: float = None

        self.authorization_numbers: float = None

        self.state_tax: float = None

        self.subtotal: float = None
        self.total: float = None
        self.fsp_eligible: float = None
        self.total_tendered: float = None
        self.change: float = None

        self.payments: list = None  # List of PaymentInfo()s. Started as None so that when entering into DB we just need to check if None.

    def append_item(self, item_id=None, receipt_alias=None, qty_sold=None, unit_price=None, ext_price=None):
        if self.items is None:
            self.items = list()

        data_to_check = [qty_sold, unit_price, ext_price]
        for data in data_to_check:
            confirm_type(data, float)

        the_item = Item(item_id=item_id, receipt_alias=receipt_alias, qty_sold=qty_sold,
                        unit_price=unit_price, ext_price=ext_price)

        self.items.append(the_item)

    def append_discount(self, receipt_alias=None, ext_price=None):
        if self.discounts is None:
            self.discounts = list()

        confirm_type(ext_price, float)

        the_discount = Discount(receipt_alias=receipt_alias, ext_price=ext_price)

        self.discounts.append(the_discount)

    def append_payments(self, card_holder_name, card_type, account_num, exp_date, amount, approval_num, current_date, reference_num):
        if self.payments is None:
            self.payments = list()

        card_type = data_after_first_char(card_type)
        account_num = data_after_first_char(account_num)
        current_date = data_after_first_char(current_date)
        exp_date = data_after_first_char(exp_date)
        confirm_type(exp_date, int)
        amount = data_after_first_char(amount)
        confirm_type(amount, float)
        approval_num = data_after_first_char(approval_num)
        reference_num = data_after_first_char(reference_num)
        confirm_type(reference_num, int)

        the_payment_info = CardInformation(card_holder_name=card_holder_name, card_type=card_type,
                                           account_num=account_num, exp_date=exp_date, amount=amount,
                                           approval_num=approval_num, current_date=current_date,
                                           reference_num=reference_num)

        self.payments.append(the_payment_info)

    def append_authorization_number(self, authorization_num):
        if self.authorization_numbers is None:
            self.authorization_numbers = list()

        authorization_num = data_after_first_char(authorization_num, char_to_split_on="#")

        self.authorization_numbers.append(authorization_num)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


def print_receipt_issue(col_num, row_num, issue_name, optional_text=None, issue_data=None):
    print(f"potential issue at {col_num_to_string(col_num)}{row_num} (col {col_num} row {row_num})"
          f" Regarding: {issue_name}", end='')
    if issue_data is not None:
        print(" (" + str(issue_data) + ")", end='')
    if optional_text is not None:
        print(" -", optional_text)
    else:
        print()


def process_receipts_rows(row_numbers, rows_of_data):
    if len(rows_of_data) != (row_numbers.end_row + 1 - row_numbers.start_row):
        raise Exception("rows of data given doesn't match row numbers for this receipt!")

    if len(rows_of_data) <= 2:
        print('2 or less rows of data at the receipt starting on l' + str(row_numbers.start_row))

    result = Receipt()
    result.position_in_excel = "a" + str(row_numbers.start_row)
    first_row = rows_of_data[0]
    second_row = rows_of_data[1]

    if first_row[0] != "Store :":
        raise Exception("Expected exactly 'Store :' at a" + str(row_numbers.start_row))

    if second_row[0] != "Item ID":
        raise Exception("Expected exactly 'Item ID' at a" + str(row_numbers.start_row + 1))

    result.store_name_header = first_row[0]
    result.start_time_header = first_row[2]
    result.end_time_header = first_row[4]
    result.invoice_number_header = first_row[6]
    result.terminal_number_header = first_row[8]
    result.customer_number_header = first_row[10]
    result.receipt_number_header = first_row[12]
    result.customer_name_header = first_row[14]
    result.cashier_name_header = first_row[16]

    result.store_name = first_row[1]
    result.start_time = first_row[3]
    result.end_time = first_row[5]
    result.invoice_number = first_row[7]
    result.terminal_number = first_row[9]
    result.customer_number = first_row[11]
    result.receipt_number = first_row[13]
    result.customer_name = first_row[15]
    result.cashier_name = first_row[17]

    # checks for issues in row 1's headers
    if result.store_name_header == "":
        print_receipt_issue(1, row_numbers.start_row, "store_name_header", "Its empty")
    if result.start_time_header == "":
        print_receipt_issue(3, row_numbers.start_row, "start_time_header", "Its empty")
    if result.end_time_header == "":
        print_receipt_issue(5, row_numbers.start_row, "end_time_header", "Its empty")
    if result.invoice_number_header == "":
        print_receipt_issue(7, row_numbers.start_row, "invoice_number_header", "Its empty")
    if result.terminal_number_header == "":
        print_receipt_issue(9, row_numbers.start_row, "terminal_number_header", "Its empty")
    if result.customer_number_header == "":
        print_receipt_issue(11, row_numbers.start_row, "customer_number_header", "Its empty")
    if result.receipt_number_header == "":
        print_receipt_issue(13, row_numbers.start_row, "receipt_number_header", "Its empty")
    if result.customer_name_header == "":
        print_receipt_issue(15, row_numbers.start_row, "customer_name_header", "Its empty")
    if result.cashier_name_header == "":
        print_receipt_issue(17, row_numbers.start_row, "cashier_name_header", "Its empty")

    # checks for issues in row 1's data values
    if result.store_name == "":  # for example HQ   Daily Table
        print_receipt_issue(2, row_numbers.start_row, "store_name", "Its empty")
    if result.start_time == "":  # 2018-10-01 11:23:43
        print_receipt_issue(4, row_numbers.start_row, "start_time", "Its empty")
    if result.end_time == "":  # 2018-10-01 11:23:43
        print_receipt_issue(6, row_numbers.start_row, "end_time", "Its empty")
    if result.invoice_number == "":  # HQ04152453
        print_receipt_issue(8, row_numbers.start_row, "invoice_number", "Its empty")
    if result.terminal_number == "":  # 4 : Terminal 4
        print_receipt_issue(10, row_numbers.start_row, "terminal_number", "Its empty")
    else:
        result.terminal_number = result.terminal_number[-1]
        confirm_type(result.terminal_number, int, row_num=row_numbers.start_row+1, col_num=10)
    if result.customer_number == "":  # EMPTY or 5084149703
        # print_receipt_issue(12, row_numbers.start_row, "customer_number", "Its empty")
        pass  # it's actually acceptable if this is empty
    if result.receipt_number == "":  # 152454.0
        print_receipt_issue(14, row_numbers.start_row, "receipt_number", "Its empty")
    if result.customer_name == "":  # EMPTY or GARTNEL, KEN
        # print_receipt_issue(16, row_numbers.start_row, "customer_name", "Its empty")
        pass  # it's actually acceptable if this is empty
    if result.cashier_name == "":  # 4574 : David
        print_receipt_issue(18, row_numbers.start_row, "cashier_name", "Its empty")

    result.item_id_header = second_row[0]
    result.receipt_alias_header = second_row[1]
    result.quantity_sold_header = second_row[2]
    result.unit_price_header = second_row[3]
    result.ext_price_header = second_row[4]

    if result.item_id_header == "":
        print_receipt_issue(1, row_numbers.start_row + 1, "item_id_header", "Its empty")
    if result.receipt_alias_header == "":
        print_receipt_issue(3, row_numbers.start_row + 1, "receipt_alias_header", "Its empty")
    if result.quantity_sold_header == "":
        print_receipt_issue(5, row_numbers.start_row + 1, "quantity_sold_header", "Its empty")
    if result.unit_price_header == "":
        print_receipt_issue(7, row_numbers.start_row + 1, "unit_price_header", "Its empty")
    if result.ext_price_header == "":
        print_receipt_issue(9, row_numbers.start_row + 1, "ext_price_header", "Its empty")

    # now we go through the remainder of the rows
    customer_name = None
    for i, row_of_data in enumerate(rows_of_data[2:]):
        # if there's something in the item id column, then we assume this is an item.
        item_id = row_of_data[0]
        if item_id != "":
            result.append_item(item_id=row_of_data[0], receipt_alias=row_of_data[1], qty_sold=row_of_data[2],
                               unit_price=row_of_data[3], ext_price=row_of_data[4])
            continue

        receipt_alias = row_of_data[1]
        current_row_in_wb = row_numbers.start_row + i + 2
        current_index_in_receipt = current_row_in_wb - row_numbers.start_row

        if receipt_alias == "--- Card Information ---":
            if "Card Type:" not in rows_of_data[current_index_in_receipt+2][1]:
                customer_name = rows_of_data[current_index_in_receipt+2][1]
        elif receipt_alias == customer_name:
            pass
        elif receipt_alias == "":
            pass
        elif receipt_alias == "No Sale":
            result.append_item(item_id=None, receipt_alias=receipt_alias, qty_sold=0, unit_price=0, ext_price=0)
        elif receipt_alias == "EBT 50% Produce DIscount":
            result.append_discount(receipt_alias=receipt_alias, ext_price=row_of_data[4])
        elif receipt_alias == "FSP ELIGIBLE":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.fsp_eligible = float(row_of_data[4])
        elif receipt_alias == "Employee Discount":
            result.append_discount(receipt_alias=receipt_alias, ext_price=row_of_data[4])
        elif receipt_alias == "$5 Coupon Applied!":
            result.append_discount(receipt_alias=receipt_alias, ext_price=row_of_data[4])
        elif receipt_alias == "Cash":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.cash = float(row_of_data[4])
        elif receipt_alias == "Debit":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.debit = float(row_of_data[4])
        elif receipt_alias == "Credit":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.credit = float(row_of_data[4])
        elif receipt_alias == "EBT":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.ebt = float(row_of_data[4])
        elif receipt_alias == "Gift Card":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.gift_card = float(row_of_data[4])
        elif receipt_alias == "EBT Cash":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.ebt_cash = float(row_of_data[4])
        elif receipt_alias == "Removed >> Cash":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.cash += float(row_of_data[4])
        elif receipt_alias == "Removed >> Credit":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.credit += float(row_of_data[4])
        elif receipt_alias == "Removed >> EBT":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.ebt += float(row_of_data[4])
        elif receipt_alias == "Removed >> Gift Card":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.credit += float(row_of_data[4])
        elif receipt_alias == "Removed >> Debit":  # theorizing here
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.debit += float(row_of_data[4])
        elif receipt_alias == "Removed >> EBT Cash":  # theorizing here
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.ebt_cash += float(row_of_data[4])
        elif receipt_alias == "SUBTOTAL":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.subtotal = float(row_of_data[4])
        elif receipt_alias == "TOTAL":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.total = float(row_of_data[4])
        elif receipt_alias == "TOTAL TENDERED":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.total_tendered = float(row_of_data[4])
        elif receipt_alias == "Change":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.change = float(row_of_data[4])
        elif receipt_alias == "State Tax":
            confirm_type(row_of_data[4], float, row_num=current_row_in_wb, col_num=5)
            result.state_tax = float(row_of_data[4])
        elif receipt_alias == "All Void":
            pass
        elif "Authorization #" in receipt_alias:
            result.append_authorization_number(receipt_alias)
        elif "Bal @" in receipt_alias:
            pass  # data is tossed
        elif "Card Type" in receipt_alias:
            pass
            # Receipt.append_payments(card_holder_name=, card_type=, account_num=, exp_date=, amount=, approval_num=, current_date=, reference_num=)
            result.append_payments(card_holder_name=rows_of_data[current_index_in_receipt-1][1],
                                   card_type=receipt_alias,
                                   account_num=rows_of_data[current_index_in_receipt+1][1],
                                   exp_date=rows_of_data[current_index_in_receipt+2][1],
                                   amount=rows_of_data[current_index_in_receipt+4][1],
                                   approval_num=rows_of_data[current_index_in_receipt+5][1],
                                   current_date=rows_of_data[current_index_in_receipt+6][1],
                                   reference_num=rows_of_data[current_index_in_receipt+8][1])
        elif "Account #" in receipt_alias:
            pass  # Covered already, see 'elif "Card Type" in receipt_alias:'
        elif "Exp Date" in receipt_alias:
            pass  # Covered already, see 'elif "Card Type" in receipt_alias:'
        elif "Amount:" in receipt_alias:
            pass  # Covered already, see 'elif "Card Type" in receipt_alias:'
        elif "Approval #" in receipt_alias:
            pass  # Covered already, see 'elif "Card Type" in receipt_alias:'
        elif "Date:" in receipt_alias:
            pass  # Covered already, see 'elif "Card Type" in receipt_alias:'
        elif "Reference #" in receipt_alias:
            if current_row_in_wb != row_numbers.end_row:
                if "Card Type:" not in rows_of_data[current_index_in_receipt + 2][1]:
                    customer_name = rows_of_data[current_index_in_receipt + 2][1]
        else:
            print("data to check out at b" + str(current_row_in_wb) + ":", receipt_alias)
    return result


@dataclass
class SalesDB:
    sales_id: int = None  # Primary key
    invoice_number: str = None  # Foreign key

    item_id: str = None
    receipt_alias: str = None
    qty_sold: float = None
    unit_price: float = None
    ext_price: float = None

@dataclass
class ReceiptsDB:
    invoice_number: str = None

    store_name: str = None
    start_time: str = None
    end_time: str = None
    terminal_number: str = None
    customer_number: str = None
    receipt_number: str = None
    customer_name: str = None
    cashier: str = None

    # to do, rest of the fields


def process_clean_csv_for_receipts(file_name):
    # credit to https://stackoverflow.com/a/16988624 This is a hacky solution for getting everything converted to str
    my_wb = pd.read_csv(file_name, header=None, converters={i: str for i in range(100)})

    all_rows = list(my_wb.itertuples(index=False, name=None))
    all_rows = all_rows[:116]

    all_receipts = []
    for receipts_rows in get_receipt_rows(wb_rows=all_rows):
        processed_receipt = process_receipts_rows(row_numbers=receipts_rows, rows_of_data=all_rows[receipts_rows.start_row - 1: receipts_rows.end_row])
        # prettyprinter(processed_receipt.__dict__)
        all_receipts.append(processed_receipt)

    all_sales_db = []
    all_receipts_db = []
    sales_id_counter = 0
    for receipt in all_receipts:
        receipt_db = ReceiptsDB(invoice_number=receipt.invoice_number, store_name=receipt.store_name,
                                 start_time=receipt.start_time, end_time=receipt.end_time,
                                 terminal_number=receipt.terminal_number, customer_number=receipt.customer_number,
                                 receipt_number=receipt.receipt_number,
                                 customer_name=receipt.customer_name, cashier=receipt.cashier_name)
        all_receipts_db.append(receipt_db)

        for sale in receipt.items:
            sales_id_counter += 1
            sale_db = SalesDB(sales_id=sales_id_counter, item_id=sale.item_id, receipt_alias=sale.receipt_alias,
                              qty_sold=sale.qty_sold, unit_price=sale.unit_price, ext_price=sale.ext_price,
                              invoice_number=receipt.invoice_number)
            all_sales_db.append(sale_db)

    '''
    for receipt in all_receipts:
        print(receipt)
    '''


def main():
    # combine_sheets(excel_file, combined_sheet_file)
    # clean_sheet(combined_sheet_file, cleaned_sheet_file)
    process_clean_csv_for_receipts(cleaned_sheet_file)


main()
#  print(possible_discounts)
