## Diary.py ordered.

## IMPORTS ### -------

import sqlite3
from datetime import datetime
import re
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import shutil
from wcwidth import wcswidth
from collections import defaultdict

#----------------------------------------------------# TABLE PROPERTIES ## ------------------------------------------------------------------------------------------------------------------------

# CREATE TABLE
def create_tables(cursor, conn):

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birthdate TEXT,
        bio TEXT
    );

    CREATE TABLE IF NOT EXISTS Memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        timestamp TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Tag (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS MemoryPerson (
        memory_id INTEGER NOT NULL,
        person_id INTEGER NOT NULL,
        PRIMARY KEY (memory_id, person_id),
        FOREIGN KEY (memory_id) REFERENCES Memory(id),
        FOREIGN KEY (person_id) REFERENCES Person(id)
    );

    CREATE TABLE IF NOT EXISTS MemoryTag (
        memory_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (memory_id, tag_id),
        FOREIGN KEY (memory_id) REFERENCES Memory(id),
        FOREIGN KEY (tag_id) REFERENCES Tag(id)
    );
    """)

    conn.commit()
#ascii art render of tables
Ascii_art = """
+-----------+    +--------------+    +------------+   +-------------+    +-------------+
|  Person   |    | MemoryPerson |    |   Memory   |   |  MemoryTag  |    |     Tag     |
+-----------+    +--------------+    +------------+   +-------------+    +-------------+
|  id  x    |    | memory_id ~  |    |     id ~   |   |~ memory_id  |    |   · id      |
|  name     |    | person_id x  |    |   title    |   |   tag_id ·  |    |     name    |
| birthdate |    +==============+    |  content   |   +=============+    | description |
|   bio     |                        | timestamp  |                      +=============+
+===========+                        | created_at |
                                     +============+
"""
#fixed width for columns in table ALL TABLE HEADERS MUST BE LOWER CASE!
fixed_widths = {
    "id": 3,
    "memory_id": 3,      
    "tag_id": 3,
    "name": 12,
    "title": 20,
    "birthdate": 10,
    "timestamp": 10,
    "created_at": 16,
    "content" : len("[content]"),
    "description" : None,
    "bio": None,
    "mcount" : 6
}

#----------------------------------------------------# STANDARDISED TABLE DISPLAY ## -------------------------------------------------------------------------------------------------------------------

#standardise character width for all characters

#pad string according to actual width to support zh and other
def pad_string(text, width):
    display_width = wcswidth(text)
    padding = max(0, width - display_width)
    return text + " " * padding

#display table
def render_table(columns, rows, dynamic_columns=None):

    if not rows:
        print("No data to display.")
        return

    if dynamic_columns is None:     #if instead dynamic_columns is set in parameters, it will persist throughout other calls of the function when modified.
        dynamic_columns = {"bio", "description"}

    # Build column index map from original to new order
    original_columns = columns.copy()
    columns = [col for col in original_columns if col not in dynamic_columns] + [col for col in original_columns if col in dynamic_columns]
    column_indices = [original_columns.index(col) for col in columns]

    # Reorder rows
    rows = [[row[i] for i in column_indices] for row in rows]


    # Calculate column widths
    col_widths = []
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    fixed_total = 0
    for col in columns:
        if col in fixed_widths and fixed_widths[col] is not None:
            w = fixed_widths[col]   #when the column has a fixed width, append that
        else:
            w = 15                  #else, write 15 to it
        col_widths.append(w)
        if col not in dynamic_columns:  #then increment the total count by the width assigned
            fixed_total += w

    #calculate terminal width available for bio
    separators = 3 * (len(columns) - 1) #the amount of space separators need, and how many separators there are
    available_for_dynamic = terminal_width - fixed_total - separators
    
    dynamic_indices = [i for i, col in enumerate(columns) if col in dynamic_columns]    #finds the index, aka position within "columns" if the columnn is within "dynamic columns"
    num_dynamic = len(dynamic_indices)

    if num_dynamic > 0:
        per_column_width = max(10, available_for_dynamic // num_dynamic)
        for inx in dynamic_indices:                                                       #for every index in dynamic indices (not int auto increment!)
            col_widths[inx] = per_column_width


    # Print header
    header = [pad_string(col, col_widths[i]) for i, col in enumerate(columns)]
    print(" | ".join(header))
    print("-" * terminal_width) #every python print ends automatically w/ a new line

    # Print rows
    for row in rows:
        line = []
        for i, item in enumerate(row):
            col = columns[i]
            value = str(item) if item is not None else "—"  #converts item into string text so it can be joined
            width = col_widths[i]

            if col == "content":
                value = "[content]" if item else "—"

            elif col in dynamic_columns and wcswidth(value) > width:
                truncated = ""
                current_width = 0
                for char in value:
                    char_width = wcswidth(char)
                    if current_width + char_width > width - 3:
                        break
                    truncated += char
                    current_width += char_width
                value = truncated + "..."


            line.append(pad_string(value, width))
            
        print(" | ".join(line))

#view table
def view_table(table_name, cursor, dynamic_columns=None):
    cursor.execute(f"PRAGMA table_info({table_name})")                  #grabs all metadata from table
    columns = [info[1] for info in cursor.fetchall()]                   #displays only the column names from metadata

    try:
        cursor.execute(f"SELECT * FROM {table_name}")                       #grabs table content
        rows = cursor.fetchall()

        print(f"\nViewing table: {table_name}")
        render_table(columns, rows, dynamic_columns)
    except sqlite3.OperationalError:
        print ("please enter a valid table name")




## INPUT VALIDATIONS ###----------------------------------------------------------------------------------------------------------------------

#validating timestamp input
def validate_timestamp(ts):
    try:
        datetime.strptime(ts, "%Y-%m-%d")
        return True
    except ValueError:
        print ("Invalid format.")
        return False

#validate name inputs, is true if valid, false otherwise
def validate_name(name, max_width = 12):
    if wcswidth(name) > max_width:
        print ("Input too long.")
        return False
    if not bool(re.match(r"^[\w\s\-’'.À-ÿ一-龥]+$", name.strip())):    # Accepts Unicode letters, spaces, hyphens
        print("Invalid format. Accepts letters, hyphens and ideograms etc.")
        return False
    return True



#-------------------------------------------------------# AUTOCOMPLETE People and Tags ### --------------------------------------------------------------------------------------------------------------------------

# predict names of ppl and tags that already exist----------------
#get existing names
def get_existing_names(table_name, cursor):
    cursor.execute(f"SELECT name FROM {table_name}")
    names = [row[0] for row in cursor.fetchall()]
    return names

#autocomplete + format validation + add new names in appropriate  (person and tag entering sheet)
def get_autocomplete_list(label, table, cursor, conn, is_memory):

    entries = []
    print(f"\n{label}:")
    print(f"• Type one {label} at a time for autocomplete")
    print(f"• Or enter multiple {label}s separated by commas (e.g. A, B, C)")
    print("• When finished, enter ↵ , then type 'done'.")


    while True:
        #populate completer each round so it can see new entries
        options = get_existing_names(table, cursor)
        completer = WordCompleter(options, ignore_case=True, match_middle=True)

        entry = prompt(f"{label}(type 'done' to finish): ", completer=completer).strip()   # gives a interactive line just like input(), then prints what is in the label (like, "Person" or "Tag" so I know what I'm entering, then compares what I enter with the "completer", an object we defined earlier with the above function)
        
        if entry.lower() == "done":
            break

        #if bulk entry
        elif "," in entry:
            names = [name.strip() for name in entry.split(",") if name.strip()]
            for name in names:
                if name in options:
                    entries.append(name)
                    #doesn't support altering existing entries bc bulk
                elif not validate_name(name) :
                    print(f"Invalid name skipped: {name}")
                    
                else:
                    ask = input(f"⚠️ New name: {name}, create new element in {table}?(Y/n)")
                    if ask.lower().strip() == "y" :
                         create_profile(name, table, cursor, conn)

        elif entry in options:
            entries.append(entry)
            if not is_memory :
                create_profile(entry, table, cursor, conn)

        elif not validate_name(entry) :
            continue

        else:
            confirm = input(f"'{entry}' is new. Add it? (Y/n): ").strip().lower()
            if confirm == "y":
                entries.append(entry)
                create_profile(entry, table, cursor, conn)
            
    return entries

#create new entries for person and tag
def create_profile(entry, table, cursor, conn):
    if table.lower() == "person":
        manage_person_profile(entry, conn, cursor)
    elif table.lower() == "tag":
        manage_tags(entry, conn, cursor)
    else:
        print(f"Err - Unknown table: {table}")
        return

## MANAGE PERSON PROFILE ## 
#functioning manage person profile function
def manage_person_profile(name, conn, cursor):
    
    #find person from name
    cursor.execute("SELECT id, birthdate, bio FROM Person WHERE name = ?", (name,))
    result = cursor.fetchone()

    #if exists
    if result:
        #return and display details
        person_id, old_birthdate, old_bio = result
        print(f"\nExisting profile for {name}:")
        print(f"  Birthdate: {old_birthdate or '—'}")
        print(f"  Bio: {old_bio or '—'}")
        print("Leave blank if you don't want to change anything.")

        #birthdate input with input validation
        while True:
            birthdate = input("Birthday (YYYY-MM-DD): ").strip()
            if not birthdate or validate_timestamp(birthdate):
                birthdate = old_birthdate
                break
            print("Invalid format.")

        #bio input
        bio = input("New bio: ").strip() or old_bio

        #apply changes
        cursor.execute("UPDATE Person SET birthdate = ?, bio = ? WHERE id = ?",(birthdate, bio, person_id))
        print("Profile updated.")

    # if not existing profile
    else:
        print(f"\nCreating new profile for '{name}'")
        while True:
            birthdate = input("Birthday (YYYY-MM-DD): ").strip()
            if not birthdate or validate_timestamp(birthdate):
                break
            print("Invalid format. Try again.")

        bio = input("Short bio: ").strip()
        cursor.execute("INSERT INTO Person (name, birthdate, bio) VALUES (?, ?, ?)",
                       (name, birthdate, bio))
        print("New profile created.")

    conn.commit()

## TAG ENTERING SHEET ##
def manage_tags(entry, conn, cursor):
    cursor.execute("SELECT id, description FROM Tag WHERE name = ?", (entry,))
    result = cursor.fetchone()

    #if existing Tag, print existing, prompt change
    if result:
        tag_id, description = result
        print(f"\nExisting tag: {entry}")
        print(f"Description: {description or '—'}")

        new_description = input("New description: ").strip() or description
        cursor.execute("UPDATE Tag SET description = ? WHERE id = ?", (new_description, tag_id))

        print ("Tag updated.")

    else:
        print(f"\nCreating new tag: {entry}")
        description = input("Tag description (optional): ").strip()
        cursor.execute("INSERT INTO Tag (name, description) VALUES (?, ?)", (entry, description))
        print("New tag created.")

    conn.commit()



#--------------------------------------------# NEW MEMORY ENTRY ## -----------------------------------------------------------------------------------------------------------------------------

#multi-line input support
def get_multiline_input(prompt ="Enter text:"):  #default prompt to fall back to
    print(prompt)
    print("Type your memory below. When you're done, write 'END' on a new line by itself.")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

#TODO CACHED IS NOT PRESENT ANYWHERE
# interactable memory entering sheet
def new_or_edit_memory (cursor, conn, mem_id = None):
    is_memory = True    #to pass to autocomplete to skip profile creation

    if mem_id:
        # only id, no cache = fallback to DB query if cached is missing
    #person
        cursor.execute("""
            SELECT name FROM Person
            JOIN MemoryPerson ON Person.id = MemoryPerson.person_id
            WHERE MemoryPerson.memory_id = ?
        """, (mem_id,))
        old_people = [row[0] for row in cursor.fetchall()]
    #tag
        cursor.execute("""
            SELECT name FROM Tag
            JOIN MemoryTag ON Tag.id = MemoryTag.tag_id
            WHERE MemoryTag.memory_id = ?
        """, (mem_id,))
        old_tags = [row[0] for row in cursor.fetchall()]
    #title, content and timestamp
        cursor.execute("SELECT title, content, timestamp, created_at FROM Memory WHERE id = ?", (mem_id,))
        result = cursor.fetchone()

        old_title, old_content, old_timestamp, created_at = result

    else:
        old_title = old_content = old_timestamp = old_people = old_tags =""


#if editing existing entry
    if mem_id:
        print(f"Editing memory nr.{mem_id}")
        print("-" * 30)

        #display memory
        display_memory(old_title, old_timestamp, old_content, old_people, old_tags, created_at)

        #title
        while True:
            title = input(f"Title [{old_title}]: ").strip() or old_title    #short circuit logic, if input is void, it returns false and promotes the second value
            if validate_name(title, max_width = 30):
                break
            print("Invalid format.")
        
        #content
        new_content = get_multiline_input("What happened?")
        content = new_content if new_content.strip() else old_content

        #timestamp
        while True:
            timestamp = input(f"Timestamp [{old_timestamp}] (YYYY-MM-DD): ").strip() or old_timestamp
            if validate_timestamp(timestamp):
                break
            print("Invalid format.")

    # People
        print("\nCurrent people related to the event:", ", ".join(old_people) if old_people else "—")
        if input("Edit people? (Y/n): ").strip().lower() == "y":
            print("Please re-enter all relevant people.")
            people = get_autocomplete_list("People", "Person", cursor, conn, is_memory)
        else:
            people = old_people
    # Tags        
        print("\nCurrent tags:", ", ".join(old_tags) if old_tags else "—")
        if input("Edit tags? (Y/n): ").strip().lower() == "y":
            print("Please re-enter all relevant tags.")
            tags = get_autocomplete_list("Tags", "Tag", cursor, conn, is_memory)
        else:
            tags = old_tags
    #delete old connections
        cursor.execute("DELETE FROM MemoryPerson WHERE memory_id = ?", (mem_id,))
        cursor.execute("DELETE FROM MemoryTag WHERE memory_id = ?", (mem_id,))
    #commit
        cursor.execute("UPDATE Memory SET title = ?, content = ?, timestamp = ? WHERE id = ?", (title, content, timestamp, mem_id))

#if new entry
    else:
        #title
        while True:
            title = input(f"Title: ").strip()
            if validate_name(title, max_width = 30):
                break
            print("Invalid format.")
        
        #content
        content = get_multiline_input("What happened?")

        #timestamp
        while True:
            timestamp = input(f"Timestamp (YYYY-MM-DD): ").strip()
            if validate_timestamp(timestamp):
                break
            print("Invalid format.")
        
        #people and tags
        people = get_autocomplete_list("People", "Person", cursor, conn, is_memory)
        tags = get_autocomplete_list("Tags", "Tag", cursor, conn, is_memory)

        #update db
        cursor.execute("INSERT INTO Memory (title, content, timestamp) VALUES (?, ?, ?)", (title, content, timestamp))
        mem_id = cursor.lastrowid

    # Link people
    for name in people:
        cursor.execute("SELECT id FROM Person WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            person_id = result[0]
            cursor.execute("INSERT OR IGNORE INTO MemoryPerson (memory_id, person_id) VALUES (?, ?)", (mem_id, person_id))
    


    # Link tags
    for tag in tags:
        cursor.execute("SELECT id FROM Tag WHERE name = ?", (tag,))
        result = cursor.fetchone()
        
        if result:
            tag_id = result[0]
            cursor.execute("INSERT OR IGNORE INTO MemoryTag (memory_id, tag_id) VALUES (?, ?)", (mem_id, tag_id))

    conn.commit()

def display_memory(title, timestamp, content, people,tags,created_at):

    print("\nMemory Details")
    print("-" * 40)
    print(f"Title: {title}")
    print(f"Date: {timestamp}")
    print(f"\nContent:\n{content}")
    print("\n")
    print(f"People: {people if people else '—'}")
    print(f"Tags: {tags if tags else '—'}")
    print(f"Created: {created_at}")


#-----------------------------------------# SEARCH FUNCTION #----------------------------------------------------------------------------------------------------

# Main search, everything gets called from here
def main_search_function(cursor, conn) :
    query = input("Search for keywords (for example alice, buys, cat): ").strip()
    queries = [kw.strip() for kw in query.split(",") if kw.strip()]

    try:
        row_limit = int(input("Maximum rows to display for each table (10 by default): ").strip() or 10)
    except ValueError:
        print("Invalid input. Using default of 10.")
        row_limit = 10

    search_person(cursor, queries, max_rows=10)
    search_tag(cursor, queries, max_rows=10)
    search_memories(cursor, queries, row_limit)

    ask = input("Would you like to modify any entries?(Y/n)")
    if ask.lower().strip() == "y" :
        table, query_id = prompt_edit_target()
        if table.lower().strip() == "memory" :
            new_or_edit_memory (cursor, conn, query_id)
        elif table.lower().strip() == "tag":
            cursor.execute("SELECT name FROM Tag WHERE id = ?", (query_id,))
            result = cursor.fetchone()
            if result :
                manage_tags(result[0], conn, cursor)
        elif table.lower().strip() == "person":
            cursor.execute("SELECT name FROM Person WHERE id = ?", (query_id,))
            result = cursor.fetchone()
            if result :
                manage_person_profile(result[0], conn, cursor)

#individual tables search
def search_person(cursor, queries=None, max_rows=10):
    score_map = defaultdict(int)
    row_map = {}

    #for reusability
    if queries is None:
        querypack = input("Search for person (comma-separated): ")
        queries = [q.strip() for q in querypack.split(",") if q.strip()]

    for query in queries:
        cursor.execute("""
            SELECT id, name, birthdate, bio
            FROM Person
            WHERE name LIKE ? OR birthdate LIKE ? OR id = ? OR bio LIKE ?
        """, (f"%{query}%", f"%{query}%", query if query.isdigit() else -1, f"%{query}%"))

        for row in cursor.fetchall():
            pid = row[0]
            row_map[pid] = row
            score_map[pid] += 1
            if row[1].strip().lower() == query.lower():
                score_map[pid] += 100

    ranked = sorted(row_map.items(), key=lambda x: score_map[x[0]], reverse=True)
    match_count = len(ranked)
    print(f"\nFound {match_count} matching people.")
    if not ranked:
        print("No matching persons found.")
        return

    if len(ranked) > max_rows:
        print(f"Showing top {max_rows} matches:")
        ranked = ranked[:max_rows]

    headers = ["ID", "Name", "Birthdate", "Bio", "Memory Count", "Memory IDs"]
    rows = []

    for pid, row in ranked:
        cursor.execute("SELECT memory_id FROM MemoryPerson WHERE person_id = ?", (pid,))
        memory_ids = [str(r[0]) for r in cursor.fetchall()]
        rows.append(list(row) + [len(memory_ids), ", ".join(memory_ids) or "—"])

    render_table(headers, rows, dynamic_columns={"Bio", "Memory IDs"})

def search_tag(cursor, queries=None, max_rows=10):
    score_map = defaultdict(int)
    row_map = {}

    if queries is None:
        querypack = input("Search for tag (comma-separated): ")
        queries = [q.strip() for q in querypack.split(",") if q.strip()]

    for query in queries:
        cursor.execute("""
            SELECT id, name, description
            FROM Tag
            WHERE name LIKE ? OR id = ? OR description LIKE ?
        """, (f"%{query}%", query if query.isdigit() else -1, f"%{query}%"))

        for row in cursor.fetchall():
            tid = row[0]
            row_map[tid] = row
            score_map[tid] += 1
            if row[1].strip().lower() == query.lower():
                score_map[tid] += 100

    ranked = sorted(row_map.items(), key=lambda x: score_map[x[0]], reverse=True)
    match_count = len(ranked)
    print(f"\nFound {match_count} matching tags.")
    if not ranked:
        print("No matching tags found.")
        return

    if len(ranked) > max_rows:
        print(f"Showing top {max_rows} matches:")
        ranked = ranked[:max_rows]

    headers = ["ID", "Name", "Description", "Memory Count", "Memory IDs"]
    rows = []

    for tid, row in ranked:
        cursor.execute("SELECT memory_id FROM MemoryTag WHERE tag_id = ?", (tid,))
        memory_ids = [str(r[0]) for r in cursor.fetchall()]
        rows.append(list(row) + [len(memory_ids), ", ".join(memory_ids) or "—"])

    render_table(headers, rows, dynamic_columns={"Description", "Memory IDs"})

def search_memories(cursor, queries = None, max_rows = 10):

    score_map = defaultdict(int)
    row_map = {}
    #exact_hits = set()

    if queries == None :
        querypack = input("Search memories by keyword (like alice, bob, canteen): ").strip()
        queries = [query.strip() for query in querypack.split(",") if query.strip()]

    for query in queries : 
        cursor.execute("""
            SELECT DISTINCT Memory.id, Memory.title, Memory.timestamp FROM Memory
            LEFT JOIN MemoryPerson ON Memory.id = MemoryPerson.memory_id
            LEFT JOIN Person ON MemoryPerson.person_id = Person.id
            LEFT JOIN MemoryTag ON Memory.id = MemoryTag.memory_id
            LEFT JOIN Tag ON MemoryTag.tag_id = Tag.id
            WHERE Memory.title LIKE ? OR Memory.content LIKE ?
                OR Person.name LIKE ? OR Tag.name LIKE ?
            ORDER BY Memory.timestamp DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

        
        for row in cursor.fetchall():   # iterates through fetched rows
            mid = row[0]
            row_map[mid] = row
            score_map[mid] += 1

    ranked = sorted(row_map.items(), key=lambda x: score_map[x[0]], reverse=True)
    match_count = len(ranked)
    print(f"\nFound {match_count} matching memories.")

    if match_count > max_rows:
        print(f"Showing top {max_rows} matches:")
        ranked = ranked[:max_rows]

    if not ranked:
        print("No matching memories found.")
        return None

    rows = []
    memory_metadata = {}

    for mem_id, row in ranked:
        title = row[1]
        timestamp = row[2]

        # Get linked people
        cursor.execute("""
            SELECT name FROM Person
            JOIN MemoryPerson ON Person.id = MemoryPerson.person_id
            WHERE MemoryPerson.memory_id = ?
        """, (mem_id,))
        people = [r[0] for r in cursor.fetchall()]

        # Get linked tags
        cursor.execute("""
            SELECT name FROM Tag
            JOIN MemoryTag ON Tag.id = MemoryTag.tag_id
            WHERE MemoryTag.memory_id = ?
        """, (mem_id,))
        tags = [r[0] for r in cursor.fetchall()]

        people_str = ", ".join(people)
        tags_str = ", ".join(tags)

        rows.append([mem_id, title, people_str, tags_str, timestamp])
        memory_metadata[mem_id] = {
            "people": people_str,
            "tags": tags_str
        }

    # Render the table
    columns = ["ID", "Title", "People", "Tags", "Timestamp"]
    render_table(columns, rows, dynamic_columns={"Title", "People", "Tags"})

    #returns found mem ids
    return {row[0] for row in rows}

#edit after search
def prompt_edit_target():
    table_completer = WordCompleter(["memory", "person", "tag"], ignore_case=True)

    print("\nWhat would you like to view/modify?")
    print("Format: [table] [id] — e.g. memory 1, person 3, tag 5")
    print("Type 'done' to exit.")

    while True:
        user_input = prompt("(Type 'done' to exit) → ", completer=table_completer).strip().lower()
        if user_input.strip().lower() == "done":
            return None, None
        try:
            table, id_str = user_input.split()  #default splits at white space
            if table not in {"memory", "person", "tag"}:
                print("Invalid table. Choose memory, person, or tag.")
                continue
            if not id_str.isdigit():
                print("ID must be a number.")
                continue
            return table, int(id_str)
        except ValueError:
            print("Format must be: [table] [id]")


#----------------------------------#SQL tool #--------------------------------------------------------------------------
def sql_terminal(cursor, conn):

    print("\nSQL Terminal — type 'exit' to quit")
    while True:
        query = input("SQL> ").strip()
        if query.lower() == "exit":
            break
        try:
            cursor.execute(query)
            if query.lower().startswith("select"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                if rows:
                    render_table(columns, rows, dynamic_columns=set(columns))
                else:
                    print("Query returned no results.")
            else:
                conn.commit()
                print("Query executed.")
        except sqlite3.Error as e:
            print(f"Error: {e}")


def main():
    conn = sqlite3.connect("memory_db.sqlite")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")


    create_tables(cursor, conn)
    print("\n        Welcome to")
    print("""
          
 ███████████                                    ██████            
▒█▒▒▒███▒▒▒█                                   ███▒▒███           
▒   ▒███  ▒  █████ ████ ████████  █████ ████  ▒███ ▒▒▒  █████ ████
    ▒███    ▒▒███ ▒███ ▒▒███▒▒███▒▒███ ▒███  ███████   ▒▒███ ▒███ 
    ▒███     ▒███ ▒███  ▒███ ▒███ ▒███ ▒███ ▒▒▒███▒     ▒███ ▒███ 
    ▒███     ▒███ ▒███  ▒███ ▒███ ▒███ ▒███   ▒███      ▒███ ▒███ 
    █████    ▒▒███████  ▒███████  ▒▒███████   █████     ▒▒███████ 
   ▒▒▒▒▒      ▒▒▒▒▒███  ▒███▒▒▒    ▒▒▒▒▒███  ▒▒▒▒▒       ▒▒▒▒▒███ 
              ███ ▒███  ▒███       ███ ▒███              ███ ▒███ 
             ▒▒██████   █████     ▒▒██████              ▒▒██████  
              ▒▒▒▒▒▒   ▒▒▒▒▒       ▒▒▒▒▒▒                ▒▒▒▒▒▒   
            Write diary in terminals, as if you were being productive. By Tomeowrrow      
""")
    print("Type a command or 'help' to see options. Type 'exit' to quit.\n")


    while True:
        command = input(">>> ").strip().lower()

        if command == "exit":
            print("Goodbye!")
            break

        elif command == "help":
            print("""
Available commands:
  tutorial           → gives you a basic idea on how to use Typyfy
  structure          → View all tables and DB structure
  view [table]       → View contents of a table (view Person/Memory/Tag)
  search             → Find stuff based on keywords and view single memory entries
  person             → Create or update a Person profile
  memory             → Create or update a Memory
  tag                → Create or update a Tag
  sql                → Open interactive SQL terminal
  exit               → exits the script
""")


        elif command == "structure" :
            print("\n"+Ascii_art + "\n")

        elif command.startswith("view "):
            table_name = command.split(" ", 1)[1]
            view_table(table_name, cursor)

        elif command == "sql":
            sql_terminal(cursor, conn)

        elif command == "person":
            print("\nManage Person Profile")
            get_autocomplete_list("Person", "Person", cursor, conn, is_memory = False)

        elif command == "memory":
            new_or_edit_memory(cursor, conn, mem_id = None)
            

        elif command == "tag" :
            print("Editing Tags")
            get_autocomplete_list("Tag", "Tag", cursor, conn, is_memory = False)

        elif command == "search" :
            main_search_function(cursor, conn)

        else:
            print("Unknown command. Type 'help' to see available options.")

    conn.close()  
    

## actually running ## --------------------------------------------------------------------------------------------------------------------
try:
    main()
except Exception as e:
    print(f"Unexpected error: {type(e).__name__} — {e}")


