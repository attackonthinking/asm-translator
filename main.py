import sys

arr = sys.argv
try:
    f = open(arr[1], "rb")
    file_arr = f.read()
    f.close()
except FileNotFoundError as e:
    print("error:" + e)
out = open(arr[2], "w")

index = {
    0x0000: "UNDEF",
    0xff00: "LORE",
    0xff01: "AFTER",
    0xff1f: "HIPROC",
    0xff20: "LOOS",
    0xff3f: "HIOS",
    0xfff1: "ABS",
    0xfff2: "COMMON",
    0xffff: "XINDEX"
}

mark = {
    0: 'NOTYPE', 1: 'OBJECT', 2: 'FUNC', 3: 'SECTION', 4: 'FILE'
}
bind = {
    0: 'LOCAL', 1: 'GLOBAL'
}
vis = {
    0: 'DEFAULT', 1: '?', 2: 'HIDDEN'
}


def bit_con(file, pos: int, sz: int = 4):
    arr = []
    for i in range(pos, pos + sz):
        arr.append(file[i])
    return int.from_bytes(arr, byteorder='little')


head_fields = {
    "e_entry": bit_con(file_arr, 0x18),
    "e_phoff": bit_con(file_arr, 0x1C),
    "e_shoff": bit_con(file_arr, 0x20),
    "e_flags": bit_con(file_arr, 0x24),
    "e_ehsize": bit_con(file_arr, 0x28, 2),
    "e_phentsize": bit_con(file_arr, 0x2A, 2),
    "e_phnum": bit_con(file_arr, 0x2C, 2),
    "e_shentsize": bit_con(file_arr, 0x2E, 2),
    "e_shnum": bit_con(file_arr, 0x30, 2),
    "e_shstrndx": bit_con(file_arr, 0x32, 2)
}

data_parse = {
    # [offset, size, addr]
    ".text": [],
    ".symtab": [],
    ".strtab": []
}

num = bit_con(file_arr, head_fields["e_shstrndx"] * head_fields["e_shentsize"] + head_fields["e_shoff"] + 0x10)
ind_sections = []
for i in range(head_fields["e_shnum"]):
    offset = bit_con(file_arr, head_fields["e_shoff"] + 40 * i)
    start = offset + num
    line = ''
    while file_arr[start] != 0:
        line += chr(file_arr[start])
        start += 1
    if line in [".text", ".symtab", ".strtab"]:
        data_parse[line].append(bit_con(file_arr, head_fields["e_shoff"] + 40 * i + 16))  # off
        data_parse[line].append(bit_con(file_arr, head_fields["e_shoff"] + 40 * i + 20))  # sz
        data_parse[line].append(bit_con(file_arr, head_fields["e_shoff"] + 40 * i + 12))  # addr

# байты .symtab
sym_parse = [file_arr[i] for i in range(data_parse[".symtab"][0], data_parse[".symtab"][0] + data_parse[".symtab"][1])]
# байты .strtab
str_parse = [file_arr[i] for i in range(data_parse[".strtab"][0], data_parse[".strtab"][0] + data_parse[".strtab"][1])]

symtable = []

offset_strtab = data_parse[".strtab"][0]

# симтейбл
i = 0
while i < len(sym_parse):
    arr = sym_parse[i: i + 16]
    offset_name = bit_con(arr, 0)
    name = ''
    cnt = offset_name + offset_strtab
    while file_arr[cnt] != 0:
        name += chr(file_arr[cnt])
        cnt += 1
    arr_c = []
    arr_c.append(name)  # 0
    arr_c.append(bit_con(sym_parse, i + 4))  # 1
    arr_c.append(bit_con(sym_parse, i + 8))  # 2
    bits_del = bin(sym_parse[i + 12])[2::].rjust(8, "0")
    arr_c.append(bind[int(bits_del[0:4], 2)])  # 3
    arr_c.append(mark[int(bits_del[4:8], 2)])  # 4
    arr_c.append(sym_parse[i + 12])  # 5
    arr_c.append(vis[sym_parse[i + 13]])  # 6
    if bit_con(sym_parse, i + 14, 2) in index:
        arr_c.append(index[bit_con(sym_parse, i + 14, 2)])
    else:
        arr_c.append(bit_con(sym_parse, i + 14, 2))
    symtable.append(arr_c)
    i += 16

print("%s %-15s %7s %-8s %-8s %-8s %6s %s" % ('Symbol', 'Value', 'Size', 'Type', 'Bind', 'Vis', 'Index', 'Name'),
      file=out)
for i in range(len(symtable)):
    print("[%4i] 0x%-15X %5i %-8s %-8s %-8s %6s %s" % (
        i, symtable[i][1], symtable[i][2], symtable[i][4], symtable[i][3], symtable[i][6], symtable[i][7],
        symtable[i][0]), file=out)

# .text

# байты .text
txt_parse = [file_arr[i] for i in range(data_parse[".text"][0], data_parse[".text"][0] + data_parse[".text"][1])]

print("\n", file=out)

registr_dict = {
    " rd": ["0110111", "0010111", "1101111"],
    " rd rs1": ["1100111", "0000011", "0010011"],
    " rd rs1 rs2": ["0110011", "1100011"]
}

names = {
    0: 'zero',
    1: 'ra',
    2: 'sp',
    3: 'gp',
    4: 'tp',
    5: 't0',
    6: 't1',
    7: 't2',
    8: 's0',
    9: 's1',
    10: 'a', 18: 's', 28: 't'
}


def el_rep(k):
    cn = ''
    names = {
        0: 'zero',
        1: 'ra',
        2: 'sp',
        3: 'gp',
        4: 'tp',
        5: 't0',
        6: 't1',
        7: 't2',
        8: 's0',
        9: 's1',
        10: 'a', 18: 's', 28: 't'
    }
    if k < 10:
        cn = names[k]
    elif 10 <= k <= 17:
        cn = names[10] + str(k - 10)
    elif 18 <= k <= 27:
        cn = names[18] + str(k - 16)
    elif 28 <= k <= 31:
        cn = names[28] + str(k - 25)
    return cn


def addition(bits):
    return -int(bits[0]) << len(bits) | int(bits, 2)


for i in range(0, len(txt_parse), 4):
    arr = [bin(x)[2:].rjust(8, '0') for x in [txt_parse[i], txt_parse[i + 1], txt_parse[i + 2], txt_parse[i + 3]][::-1]]
    code = ''.join(arr)
    name = ''
    if code[-7:] == "0110111":
        name = 'LUI'
    elif code[-7:] == "0010111":
        name = 'AUIPC'
    elif code[-7:] == "1101111":
        name = 'JAL'
    elif code[-7:] == "1100111":
        name = 'JALR'
    elif code[-7:] == "1100011":
        if code[-15:-12] == "000":
            name = "BEQ"
        elif code[-15:-12] == "001":
            name = "BNE"
        elif code[-15:-12] == "100":
            name = "BLT"
        elif code[-15:-12] == "101":
            name = "BGE"
        elif code[-15:-12] == "110":
            name = "BLTU"
        elif code[-15:-12] == "111":
            name = "BGEU"
    elif code[-7:] == "0000011":
        if code[-15:-12] == "000":
            name = "LB"
        elif code[-15:-12] == "001":
            name = "LH"
        elif code[-15:-12] == "010":
            name = "LW"
        elif code[-15:-12] == "100":
            name = "LBU"
        elif code[-15:-12] == "101":
            name = "LHU"
    elif code[-7:] == "0100011":
        if code[-15:-12] == "000":
            name = "SB"
        elif code[-15:-12] == "001":
            name = "SH"
        elif code[-15:-12] == "010":
            name = "SW"
    elif code[-7:] == "0010011":
        if code[-15:-12] == "000":
            name = "ADDI"
        elif code[-15:-12] == "010":
            name = "SLTI"
        elif code[-15:-12] == "011":
            name = "SLTIU"
        elif code[-15:-12] == "100":
            name = "XORI"
        elif code[-15:-12] == "110":
            name = "ORI"
        elif code[-15:-12] == "111":
            name = "ANDI"
        elif code[-15:-12] == "001":
            name = "SLLI"
        elif code[-15:-12] == "101":
            if code[1] == "0":
                name = "SRLI"
            elif code[1] == "1":
                name = "SRAI"
    elif code[-7:] == "0110011":
        if code[-15:-12] == "000":
            if code[1] == "0":
                name = "ADD"
            elif code[1] == "1":
                name = "SUB"
            elif code[6] == "1":
                name = "MUL"
        elif code[-15:-12] == "001":
            if code[6] == "1":
                name = "MUlH"
            else:
                name = "SLL"
        elif code[-15:-12] == "010":
            if code[6] == "1":
                name = "MULHSU"
            else:
                name = "SLT"
        elif code[-15:-12] == "011":
            if code[6] == "1":
                name = "MULHU"
            else:
                name = "SLTU"
        elif code[-15:-12] == "100":
            if code[6] == "1":
                name = "DIV"
            else:
                name = "XOR"
        elif code[-15:-12] == "101":
            if code[1] == "0":
                name = "SRL"
            elif code[6] == 1:
                name = "DIVU"
            elif code[1] == "1":
                name = "SRA"
        elif code[-15:-12] == "110":
            if code[1] == "1":
                name = "REM"
            else:
                name = "OR"
        elif code[-15:-12] == "111":
            if code[6] == "1":
                name = "REMU"
            else:
                name = "AND"
    elif code[-7:] == "1110011":
        if code[11] == "0":
            name = "ECALL"
        elif code[11] == "1":
            name = "EBREAK"
    if name in ["SLLI", "SRLI", "SRAI"]:
        name += " " + str(el_rep(int(code[-12:-7], 2))) + " " + str(el_rep(int(code[-20:-15], 2))) + " " + str(
            addition(code[-25:-20]))
    elif code[-7:] in registr_dict[" rd rs1 rs2"]:
        name += " " + str(el_rep(int(code[-12:-7], 2))) + " " + str(el_rep(int(code[-20:-15], 2))) + " " + str(
            el_rep(int(code[-25:-20], 2)))
    elif code[-7:] in registr_dict[" rd rs1"]:
        name += " " + str(el_rep(int(code[-12:-7], 2))) + " " + str(el_rep(int(code[-20:-15], 2)))
    elif code[-7:] in registr_dict[" rd"]:
        name += " " + str(el_rep(int(code[-12:-7], 2)))
    print(name, file=out)
