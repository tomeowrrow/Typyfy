
Thank you for using:
 
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
The SQLite-backed command-line interface that lets you write diary in terminal, as though you were testing code or smth.

Don't you hate it when you really want to start writing diary, but don't have the time for it bc of work?
Or you'd like to feel like a '90s hacker while annotating gossip.
Or maybe you just have really nosy family members.
Then Typyfy is for you! Use the magical power of the command-line interface to repel technically unsavvy housemates, suspicious superiors and the diary-writing-connected pinkish prejudices.

## Features

- Create, update, and view:
  - **Person** profiles with birthdate and bio
  - **Memory** entries with timestamped content
  - **Tags** for thematic organization
- Link memories to people and tags
- Search across all entities with keyword scoring
- View related memory IDs and counts per person/tag
- Interactive SQL terminal for advanced queries
- Clean tabular rendering with dynamic column wrapping

## Requirements

- Python 3.8+
- SQLite3
- pip install -r requirements.txt

## Commands

| Command         | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `structure`     | View all tables and database structure                                      |
| `view [table]`  | View contents of a table (`Person`, `Memory`, `Tag`)                        |
| `person`        | Create or update a person profile                                           |
| `memory`        | Create or update a memory entry                                             |
| `tag`           | Create or update a tag                                                      |
| `search`        | Search across memories, people, and tags by keyword                         |
| `sql`           | Open an interactive SQL terminal                                            |
| `exit`          | Exit the CLI                                                                |

## Table structure

+-----------+    +--------------+    +------------+   +-------------+    +-------------+
|  Person   |    | MemoryPerson |    |   Memory   |   |  MemoryTag  |    |     Tag     |
+-----------+    +--------------+    +------------+   +-------------+    +-------------+
|  id  x    |    | memory_id ~  |    |     id ~   |   |~ memory_id  |    |   · id      |
|  name     |    | person_id x  |    |   title    |   |   tag_id ·  |    |     name    |
| birthdate |    +==============+    |  content   |   +=============+    | description |
|   bio     |                        | timestamp  |                      +=============+
+===========+                        | created_at |
                                     +============+
