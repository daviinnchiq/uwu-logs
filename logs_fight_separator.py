from collections import defaultdict
import logging
import logs_main
import constants
MUTLIBOSSES = constants.MUTLIBOSSES
ANOTHER_BOSSES = {y:x[0] for x in MUTLIBOSSES.values() for y in x[1:]}
BOSSES_GUIDS = set(ANOTHER_BOSSES) | set(ANOTHER_BOSSES.values()) | set(constants.BOSSES_GUIDS)
FLAGS = {'UNIT_DIED', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE', 'SPELL_AURA_APPLIED', 'SPELL_HEAL'}
IGNORED_IDS = {
    '56190', '56191', '55346', #Lens
    '60122', # Baby Spice
    '53338', '1130', '14323', '14324', '14325', '19421', '19422', '19423', # Hunter's Mark
    '70861', '72550', '72273', '72371', '70952', '72443', '72410',
}

def convert_to_names(data: dict):
    B = {guids[0]:name for name, guids in MUTLIBOSSES.items()}
    return {B.get(x, constants.BOSSES_GUIDS[x]): y for x,y in data.items()}

@constants.running_time
def dump_all_boss_lines(logs: list[str]):
    # _bosses: dict[str, list[tuple[int, list[str]]]] = {}
    _bosses: dict[str, list[tuple[int, list[str]]]] = defaultdict(list)
    for n, line in enumerate(logs):
        line = line.split(',')
        if line[1] not in FLAGS:
            continue
        if line[2] == line[4]:
            continue
        # if "BUFF" in line:
        if line[-1] == "BUFF":
            continue
        # if "72350" in line:
        #     s_guid = line[2][6:-6]
        #     if s_guid == "008EF5":
        #         _bosses[s_guid].append((n, line))
        #         continue
        
        try:
            if line[6] in IGNORED_IDS:
                continue
        except IndexError:
            pass
        
        _guid = line[4][6:-6]
        if _guid not in BOSSES_GUIDS:
            _guid = line[2][6:-6]
            if _guid not in BOSSES_GUIDS:
                continue
        _guid = ANOTHER_BOSSES.get(_guid, _guid)
        _bosses[_guid].append((n, line))
    return _bosses

@constants.running_time
def dump_all_boss_lines2(logs: list[str]):
    _bosses: dict[str, list[tuple[int, list[str]]]] = {}
    for n, line in enumerate(logs):
        if ",BUFF" in line:
            continue
        line = line.split(',')
        target_guid = line[4][6:-6]
        if target_guid not in BOSSES_GUIDS:
            continue
        if line[1] not in FLAGS:
            continue
        if line[2] == line[4]:
            continue
        try:
            if line[6] in IGNORED_IDS:
                continue
        except IndexError:
            pass
        target_guid = ANOTHER_BOSSES.get(target_guid, target_guid)
        _bosses.setdefault(target_guid, []).append((n, line))
    return _bosses

@constants.running_time
def dump_all_boss_lines3(logs: list[str]):
    _bosses: dict[str, list[tuple[int, list[str]]]] = {}
    for n, line in enumerate(logs):
        if ",BUFF" in line:
            continue
        _, flag, sGUID, _, tGUID, _, *a = line.split(',', 7)
        tGUID_id = tGUID[6:-6]
        if tGUID_id not in BOSSES_GUIDS:
            continue
        if flag not in FLAGS:
            continue
        if sGUID == tGUID:
            continue
        
        try:
            if a[0] in IGNORED_IDS:
                continue
        except IndexError:
            pass
        tGUID_id = ANOTHER_BOSSES.get(tGUID_id, tGUID_id)
        _bosses.setdefault(tGUID_id, []).append((n, line))
    return _bosses

def get_more_precise(times: list[tuple[int, list[str]]], limit: int):
    if "UNIT_DIED" in times[-1][1]:
        return times
    lines = [x[1] for x in times[-limit:]][:-1]
    for n, line in enumerate(reversed(lines)):
        if "UNIT_DIED" in line:
            return times[:-n-1]
    
    for n, line in enumerate(lines):
        if line[1] == 'SPELL_AURA_APPLIED':
            continue
        if line[10] != "0":
            return times[:n-limit+1]
    
    return times

def time_pairs(times: tuple[int, list[str]], boss_name):
    # if boss_name == "Sindragosa":
    #     print(times[:100])
    # 1st + last line and if delta between lines > 100 sec separate to tries
    last_index, line = times[0]
    indexes: set[int] = {last_index-1, }
    last_time_dt = constants.to_dt(line[0])

    times = get_more_precise(times, 20)
    last_index = times[-1][0]
    indexes.add(last_index)

    for line_index, line in times:
        _now = constants.to_dt(line[0])
        if _now - last_time_dt > constants.T_DELTA:
            indexes.add(last_index)
            indexes.add(line_index-1)
        last_time_dt = _now
        last_index = line_index

    sorted_indexes = sorted(indexes)

    # if len(sorted_indexes) % 2:
    #     print(boss_name)
    #     print(times[0])
    #     print(times[-1])
    #     print(f"indexes: {sorted_indexes}\n")

    return list(zip(sorted_indexes[::2], sorted_indexes[1::2]))


def time_pairs(times: tuple[int, list[str]], boss_name):
    # if boss_name == "Sindragosa":
    #     print(times[:100])
    # 1st + last line and if delta between lines > 100 sec separate to tries
    last_index, line = times[0]
    indexes: set[int] = {last_index, }
    last_time_dt = constants.to_dt(line[0])

    times = get_more_precise(times, 20)
    _index = times[-1][0]
    indexes.add(_index+1)
    _last_line = ""
    for line_index, line in times:
        _now = constants.to_dt(line[0])
        # if '72350' in line and '0008EF5' in line[2] and line[1] != 'SPELL_CAST_START':
        #     #  and '0008EF5' in line and 'SPELL_CAST_START' not in line):
        #     print(_last_line)
        #     indexes.add(last_index+1)
        #     indexes.add(line_index)
        # el
        if _now - last_time_dt > constants.T_DELTA:
            indexes.add(last_index+1)
            indexes.add(line_index)
        _last_line = line
        last_time_dt = _now
        last_index = line_index

    sorted_indexes = sorted(indexes)

    # if len(sorted_indexes) % 2:
    #     print(boss_name)
    #     print(times[0])
    #     print(times[-1])
    #     print(f"indexes: {sorted_indexes}\n")

    return list(zip(sorted_indexes[::2], sorted_indexes[1::2]))

@constants.running_time
def filter_bosses(filtered_logs: dict[str, tuple]):
    return {
        boss_name: time_pairs(times, boss_name)
        for boss_name, times in filtered_logs.items()
        if times
    }

def find_fof(logs_slice):
    for n, line in enumerate(logs_slice):
        if '72350' in line and '0008EF5' in line and 'SPELL_CAST_START' not in line: # Fury of Frostmourne
            return n

def refine_lk(data, logs): # precise LK split at FOF
    if 'The Lich King' not in data:
        return
    LK = data['The Lich King']
    last_s, last_f = LK[-1]
    if len(LK) == 1:
        # print('[refine_lk] len(LK) == 1')
        i = -2
    else:
        # print('[refine_lk] len(LK) >= 2')
        prelast_s, prelast_f = LK[-2]
        shifted_f = max(0, prelast_f-5000)
        logs_slice = logs[shifted_f:prelast_f]
        fof = find_fof(logs_slice)
        if fof is not None:
            # print('[refine_lk] fof is not None')
            LK[-2:] = [(prelast_s, shifted_f+fof+1), (shifted_f+fof, last_f)]
            return
        # print('[refine_lk] fof is None')
        i = -1

    logs_slice = logs[last_s:last_f]
    fof = find_fof(logs_slice)
    if fof is not None:
        LK[i:] = [(last_s, last_s+fof+1), (last_s+fof, last_f)]

def remove_short_tries(data: dict[str, list[tuple[int, int]]], logs):
    for pairs in data.values():
        for pair in list(pairs):
            s = logs[pair[0]]
            f = logs[pair[1]]
            if constants.get_time_delta(s, f) < constants.T_DELTA_SHORT:
                pairs.remove(pair)
                print('REMOVED:', pair)

@constants.running_time
def main(logs):
    _all_boss_lines = dump_all_boss_lines(logs)
    # _all_boss_lines = dump_all_boss_lines(logs)
    # _all_boss_lines = dump_all_boss_lines(logs)
    # _all_boss_lines = dump_all_boss_lines(logs)
    # _all_boss_lines = dump_all_boss_lines(logs)
    # _all_boss_lines = dump_all_boss_lines(logs)
    # for n, line in _all_boss_lines['008EF5']:
    #     if n < 470681:
    #         print(n, line)
    _all_boss_lines_names = convert_to_names(_all_boss_lines)
    data = filter_bosses(_all_boss_lines_names)
    refine_lk(data, logs)
    remove_short_tries(data, logs)
    return data


def __redo(name):
    print(name)
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    path = report.relative_path("ENCOUNTER_DATA")
    data = main(logs)
    constants.json_write(path, data, indent=None)

def __redo_wrapped(name):
    try:
        __redo(name)
    except Exception:
        logging.exception(f'logs_fight_sep __redo {name}')

if __name__ == '__main__':
    # __redo("22-06-17--20-57--Nomadra")
    # print()
    # constants.redo_data(__redo_wrapped, startfrom="22-03-12--04-16--Katianei", end="22-03-12--23-44--Plugr")
    constants.redo_data(__redo_wrapped)