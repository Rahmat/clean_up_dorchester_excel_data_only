import pandas as pd

excel_file = "C:/Users/R1/Downloads/f.xls"

output_folder = "C:/Users/R1/Desktop/tmp/"
combined_sheet_file = output_folder + "combined.csv"
output_filename = "test2.csv"
output_file = output_folder + output_filename

total_number_of_receipts = 0

organized_transactions = pd.DataFrame()

possible_discounts = []
#possible_payment_methods = []


def col_num_to_string(n):
    # Full credit to https://stackoverflow.com/a/23862195/8333189
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def combine_sheets(input_file_name, output_file_name):
    input_workbook = pd.read_excel(input_file_name, sheet_name=None, ignore_index=True, header=None)

    combined_sheets = pd.concat(input_workbook.values())

    combined_sheets.to_csv(output_file_name, index=False, header=False)


'''RECEIPT LAYOUT
    Transaction info
    Headers
    
    Items
    
    Discounts
    
    Subtotal
    Payment type
    Total
    FSP Eligibility (is what category?)
    Total tendered
    Change
    
    Card Info
    
    Amount
    Approval#
    Date (seems like a repeat of transaction end time)
'''


class PaymentInfo:
    possible_types = ["Credit", "Debit", "Cash", "EBT"]

    def __init__(self):
        self.discounts: list = None  # Employee Discount

        self.type: str = None  # see possible_types
        self.subtotal: str = None
        self.total: str = None
        self.fsp_eligible: str = None
        self.total_tendered: str = None
        self.change: str = None

        self.card_holder_name: str = None  # doesnt seem to be there for ebt
        self.card_type: str = None  # Remove 'Card Type: '
        self.account_num: str = None  # Remove 'Account #: '
        self.exp_date: str = None  # Remove 'Exp Date : '

    def append_discount(self, discount):
        if self.discounts is None:
            self.discounts = list()

        if type(discount) != dict:
            print('discount was not a dict, not appending this to self.discounts')
        else:
            self.discounts.append(discount)


class Item:
    def __init__(self):
        self.item_id: str = None
        self.receipt_alias: str = None
        self.qty_sold: float = None
        self.unit_price: float = None
        self.ext_price: float = None


class Receipt:
    def __init__(self):
        self.store_name: str = None
        self.start_time: str = None
        self.end_time: str = None
        self.invoice_number: str = None
        self.terminal_number: str = None
        self.customer_number: str = None
        self.receipt_number: str = None
        self.customer_name: str = None
        self.cashier_name: str = None

        self.items: dict = None  # Dict of Item()s

        self.payment_info = PaymentInfo()

        self.amount: float = None  # Remove "Amount: "
        self.approval_number = None  # Remove "Approval #: "
        self.date: str = None  # Remove "Date: "

        self.reference_number: int = None  # Remove "Reference #: "
    
    def append_item(self, item_id=None, receipt_alias=None, qty_sold=None, unit_price=None, ext_price=None):
        if self.items is None:
            self.items = list()

        self.items.append([item_id, receipt_alias, qty_sold, unit_price, ext_price])


def print_receipt_issue(col_num, row_num, issue_name, optional_text=None):
    print(f"potential issue at {col_num_to_string(col_num)}{row_num} (col {col_num} row {row_num})"
          f" Regarding: {issue_name}", end='')
    if optional_text is not None:
        print(" -", optional_text)
    else:
        print()


def process_receipt_rows(starting_row, ending_row, all_rows):
    global total_number_of_receipts
    global organized_transactions
    total_number_of_receipts += 1
    print(starting_row, "to", ending_row)

    receipt_rows = all_rows[starting_row-1:ending_row]

    first_row = receipt_rows[0]
    my_receipt = Receipt()

    store_name_header = first_row[0]
    start_time_header = first_row[2]
    end_time_header = first_row[4]
    invoice_number_header = first_row[6]
    terminal_number_header = first_row[8]
    customer_number_header = first_row[10]
    receipt_number_header = first_row[12]
    customer_name_header = first_row[14]
    cashier_name_header = first_row[16]

    store_name = first_row[1]
    start_time = first_row[3]
    end_time = first_row[5]
    invoice_number = first_row[7]
    terminal_number = first_row[9]
    customer_number = first_row[11]
    receipt_number = first_row[13]
    customer_name = first_row[15]
    cashier_name = first_row[17]

    if store_name_header == "":
        print_receipt_issue(1, starting_row, "store_name_header", "Its empty")
    if start_time_header == "":
        print_receipt_issue(3, starting_row, "start_time_header", "Its empty")
    if end_time_header == "":
        print_receipt_issue(5, starting_row, "end_time_header", "Its empty")
    if invoice_number_header == "":
        print_receipt_issue(7, starting_row, "invoice_number_header", "Its empty")
    if terminal_number_header == "":
        print_receipt_issue(9, starting_row, "terminal_number_header", "Its empty")
    if customer_number_header == "":
        print_receipt_issue(11, starting_row, "customer_number_header", "Its empty")
    if receipt_number_header == "":
        print_receipt_issue(13, starting_row, "receipt_number_header", "Its empty")
    if customer_name_header == "":
        print_receipt_issue(15, starting_row, "customer_name_header", "Its empty")
    if cashier_name_header == "":
        print_receipt_issue(17, starting_row, "cashier_name_header", "Its empty")

    if store_name == "":  # HQ   Daily Table
        print_receipt_issue(2, starting_row, "store_name", "Its empty")
    if start_time == "":  # 2018-10-01 11:23:43
        print_receipt_issue(4, starting_row, "start_time", "Its empty")
    if end_time == "":  # 2018-10-01 11:23:43
        print_receipt_issue(6, starting_row, "end_time", "Its empty")
    if invoice_number == "":  # HQ04152453
        print_receipt_issue(8, starting_row, "invoice_number", "Its empty")
    if terminal_number == "":  # 4 : Terminal 4
        print_receipt_issue(10, starting_row, "terminal_number", "Its empty")
    if customer_number == "":  # EMPTY or 5084149703
        # print_receipt_issue(12, starting_row, "customer_number", "Its empty")
        pass
    if receipt_number == "":  # 152454.0
        print_receipt_issue(14, starting_row, "receipt_number", "Its empty")
    if customer_name == "":  # EMPTY or GARTNEL, KEN
        # print_receipt_issue(16, starting_row, "customer_name", "Its empty")
        pass
    if cashier_name == "":  # 4574 : David
        print_receipt_issue(18, starting_row, "cashier_name", "Its empty")

    my_receipt.store_name = store_name
    my_receipt.start_time = start_time
    my_receipt.end_time = end_time
    my_receipt.invoice_number = invoice_number
    my_receipt.terminal_number = terminal_number
    my_receipt.customer_number = customer_number
    my_receipt.receipt_number = receipt_number
    my_receipt.customer_name = customer_name
    my_receipt.cashier_name = cashier_name

    second_row = all_rows[starting_row]

    item_id_header = second_row[0]
    receipt_alias_header = second_row[1]
    quantity_sold_header = second_row[2]
    unit_price_header = second_row[3]
    ext_price_header = second_row[4]

    payment_info_start: str = None
    for i, row_data in enumerate(receipt_rows[2:], 2):
        tmp_item_id = row_data[0]
        tmp_receipt_alias = row_data[1]
        if tmp_item_id == '' and tmp_receipt_alias != 'No Sale':
            # this would be the (i+1)th row in the receipt, due to 0 indexing in python vs 1 indexing in excel
            payment_info_start = i
            break

        tmp_qty_sold = row_data[2]
        tmp_unit_price = row_data[3]
        tmp_ext_price = row_data[4]
        my_receipt.append_item(item_id=tmp_item_id, receipt_alias=tmp_receipt_alias, qty_sold=tmp_qty_sold,
                               unit_price=tmp_unit_price, ext_price=tmp_ext_price)

        del tmp_item_id, tmp_receipt_alias, tmp_qty_sold, tmp_unit_price, tmp_ext_price

    if payment_info_start is not None:
        # until you hit ebt/credit/debit/cash, you're processing discounts(?)
        discounts_end: str = None
        for i, row_data in enumerate(receipt_rows[payment_info_start:], payment_info_start):
            print(i, row_data)
            tmp_discount_name = row_data[1]
            if any(string in tmp_discount_name for string in my_receipt.payment_info.possible_types):
                discounts_end = i
                break
            print(tmp_discount_name)
            if "Discount" not in tmp_discount_name:
                print_receipt_issue(3, starting_row + payment_info_start, "tmp_discount_name",
                                    "Does not contain the word 'Discount'")
            if tmp_discount_name not in possible_discounts:
                possible_discounts.append(tmp_discount_name)
            tmp_qty_sold = row_data[2]
            tmp_unit_price = row_data[3]
            tmp_ext_price = row_data[4]
            my_receipt.payment_info.append_discount({"Receipt Alias": tmp_discount_name, "Quantity Sold": tmp_qty_sold,
                                                     "Unit Price": tmp_unit_price, "Ext Price": tmp_ext_price})
            # print(tmp_qty_sold)


def process_converted_csv_for_receipts(file_name):
    # credit to https://stackoverflow.com/a/16988624 This is a hacky solution for getting everything converted to str
    my_wb = pd.read_csv(file_name, header=None, converters={i: str for i in range(100)})

    all_rows = list(my_wb.itertuples(index=False, name=None))

    start_row: int = None
    for i, row_data in enumerate(all_rows[:35000]):
        # we're assuming the receipt has ended once we hit the next "Store"
        if row_data[0] != "Store :":
            continue

        if start_row is not None:
            end_row = i
            process_receipt_rows(start_row, end_row, all_rows)

        # we're adding 1 to each row number because rows are 1 indexed
        start_row = i + 1
    # process_receipt_rows(start_row, len(all_rows))

    print(total_number_of_receipts, "receipts found")


def main():
    combine_sheets(excel_file, combined_sheet_file)
    process_converted_csv_for_receipts(combined_sheet_file)


main()
print(possible_discounts)