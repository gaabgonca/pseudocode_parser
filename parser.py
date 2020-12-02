import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
import pandas as pd

#This functions returns the lines from a .txt file
def get_lines(filename):
    file = open(filename, 'r+')
    lines = file.readlines()
    lines = map(lambda line : line[:-1],lines)
    file.close()
    return lines

def get_type(line):
    #If not line.lower().find('x') returns true if x starts at line[0] 
    if not line.lower().find('inicio'):
        return "inicio"
    if not line.lower().find('pare'):
        return "pare"
    if not line.lower().find('para'):
        return "para"
    if not line.lower().find('lea'):
        return "lea"
    if not line.lower().find('esc'):
        return "esc"
    if not line.lower().find('fpara'):
        return "fpara"
    if not line.lower().find('sino'):
        return "sino"
    if not line.lower().find('si'):
        return "si"
    if not line.lower().find('fsi'):
        return "fsi"
    if line.lower().find('='):
        return "assignment"
    return "Indefinite so far"

def process_for(line):
        raw_data = line[line.index('=')+1:]
        split_data = raw_data.split(',')
        lower_bound = parse_expr(split_data[0])
        upper_bound = parse_expr(split_data[1])
        increment = parse_expr(split_data[2])
        return {
            'lower_b' : lower_bound,
            'upper_b' : upper_bound,
            'inc' : increment
        }

def process_if(line):
    comparisons = [pos for pos, char in enumerate(line) if char == '(']
    return {
        'comparisons' : len(comparisons)
    }

def new_get_statement_runtime(syntax):
    lines_dict_list = lines = syntax.to_dict('records')
    order = 0
    for index in range(len(lines_dict_list)):
        line = lines[index]
        line_type = line['type']
        if line_type in ('inicio','pare','sino'):
            #order does not change
            line['runtime'] = 0
            line['order'] = order
        elif line_type in ("assignment",'lea','esc'):
            line['runtime'] = 1
            line['order'] = order
        elif  line_type in ('fsi','fpara'):
            order -= 1
            line['runtime'] = 0
            line['order'] = order
        elif line_type is 'para':
            line['runtime'] = 'Nan'
            line['data'] = process_for(line['line'])
            line['order'] = order
            order += 1
        elif line_type is 'si':
            line['runtime'] = 'Nan' 
            line['data'] = process_if(line['line'])
            line['order'] = order
            order +=1

    
    return pd.DataFrame.from_dict(lines)

def get_if_block_runtime(block_lines):
    runtime = 0
    for line in block_lines:
        runtime += line['runtime']
    return runtime

def get_if_blocks_runtime(syntax):
    lines_dict_list = lines = syntax.to_dict('records')
    if_indices = [pos for pos, line in enumerate(lines) if line['type'] is 'si']
    else_indices = [pos for pos, line in enumerate(lines) if line['type'] is 'sino']
    end_if_indices = [pos for pos, line in enumerate(lines) if line['type'] is 'fsi']
    # done = False

    #Let's begin by processing the ifs statements
    if_statements = []
    for x, if_index in enumerate(if_indices):
        #Find closing endif
        end_if_index = end_if_indices[x]
        #Is there an else?
        else_index = False
        for line_index in range(if_index,end_if_index):
            if  line_index in else_indices:
                else_index = line_index
                break
        # print((if_index,else_index,end_if_index))
        comparisons = lines[if_index]['data']['comparisons']
        if_runtime = comparisons
        if else_index:
            block_a = lines[if_index+1:else_index]
            block_b = lines[else_index+1: end_if_index]
            bloc_a_runtime = get_if_block_runtime(block_a)
            bloc_b_runtime = get_if_block_runtime(block_b)
            if_runtime += max(bloc_a_runtime,bloc_b_runtime)
        else:
            block = lines[if_index+1:end_if_index]
            bloc_runtime = get_if_block_runtime(block)
            if_runtime += bloc_runtime
        # print((if_index,else_index,end_if_index,if_runtime))
        lines[if_index]['runtime'] = if_runtime
    return pd.DataFrame.from_dict(lines)

def for_runtime_formula(for_data,content_runtime):
    lower_bound = for_data['lower_b']
    upper_bound = for_data['upper_b']
    try:
        lower_bound = int(lower_bound)
    except TypeError:
        lower_bound = lower_bound
    try: 
        upper_bound = int(upper_bound)
    except TypeError:
        upper_bound = upper_bound

    increment = parse_expr(str(for_data['inc']))
    if increment < 0:
        lower_bound, upper_bound = upper_bound, lower_bound
        increment = -1 * increment
    # ceil = sp.Function('ceil')
    iterations = (((upper_bound-lower_bound+1)/increment)*(content_runtime +2)) + 2
    return iterations  

def get_for_blocks_runtime(syntax):
    lines_dict_list = lines = syntax.to_dict('records')
    for_indices = [pos for pos, line in enumerate(lines) if line['type'] is 'para']
    # print('for_indices',for_indices)
    endfor_indices = [pos for pos,line in enumerate(lines) if line['type'] is 'fpara']
    # print('endfor_indices',endfor_indices)
    #get for blocks and their orders
    block_orders = []
    for x ,for_index in enumerate(for_indices):
        if x < len(for_indices) -1 :
            next_end_for = endfor_indices[x]
            next_for = for_indices[x+1]
            if next_for < next_end_for:
                block_orders.append((for_index,0))
            else:
                block_orders.append((for_index,1))
        else:
            block_orders.append((for_index,1))
    # print(block_orders)

    #get inner for runtime
    for for_index in [bloc_order[0] for bloc_order in block_orders if bloc_order[1] is 1]:
        # print(for_index)
        for end_for in endfor_indices:
            if end_for > for_index:
                break
        for_order = lines[for_index]['order']
        instruction_order = for_order + 1
        inner_instructions = lines[for_index+1:end_for]
        content_runtime = 0 #placeholder
        for line in inner_instructions:
            #Selects elements that have +1 order above the loop
            if(line['order'] is instruction_order):
                content_runtime+= line['runtime']
        for_runtime = for_runtime_formula(lines[for_index]['data'],content_runtime)
        lines[for_index]['runtime'] = for_runtime
    

    #get outer for runtimes
    for for_index in [bloc_order[0] for bloc_order in block_orders if bloc_order[1] is 0]:
        for x, end_for in enumerate(endfor_indices):
            if lines[end_for]['order'] == lines[for_index]['order'] and end_for >for_index:
                break
        for_order = lines[for_index]['order']
        instruction_order = for_order + 1
        inner_instructions = lines[for_index+1:end_for]
        content_runtime = "" #placeholder
        for line in inner_instructions:
            #selects instructions that are 1 order above the for loop line order
            if(line['order'] is instruction_order):
                content_runtime += '+'+str(line['runtime'])
        for_runtime =for_runtime_formula(lines[for_index]['data'],parse_expr(str(content_runtime)))
        lines[for_index]['runtime'] = for_runtime 
    return pd.DataFrame.from_dict(lines)

def calculate_runtime(syntax_complete):
    lines = syntax_complete.to_dict('records')
    runtime = parse_expr('0')
    for line in lines:
        if line['order'] is 0:
            runtime += line['runtime']
    return sp.simplify(runtime)

def get_total_runtime(lines):
    syntax = pd.DataFrame(data=lines, columns=['line'])
    syntax["length"] = syntax["line"].map(lambda line: len(line))
    syntax["type"] = syntax["line"].map(get_type)
    new_syntax = new_get_statement_runtime(syntax)
    syntax_with_ifs = get_if_blocks_runtime(new_syntax)
    syntax_complete = get_for_blocks_runtime(syntax_with_ifs)
    runtime = calculate_runtime(syntax_complete)
    return (runtime, syntax_complete)

