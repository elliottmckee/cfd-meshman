
def write_mapbc(filename, tags, bctypes, names):

    lines = [f'{tag}\t{bc}\t{name}\n' for tag, bc, name in zip(tags, bctypes, names)]

    with open(filename, 'w') as f:
        f.write(f'{len(tags)}\n')
        f.writelines(lines)

if __name__ == '__main__':
    write_mapbc('t16.mapbc', tags=[1,3], bctypes=[3000, 5050],names=['wall', 'farfield'])
