import re

class Character:
    def __init__(self, room):
        self.inventory = []
        self.room = room
        self.callbacks = {}

    def on(self, action_name, reaction):
        self.callbacks[action_name] = reaction

class Object:
    def __init__(self, name, description, actions):
        self.name = name
        self.description = description
        self.actions = actions
        self.callbacks = {}
        
    def __repr__(self):
        return self.name

    def tokenize(self):
        return self.name.split(' ')
    
    def on(self, action_name, reaction):
        self.callbacks[action_name] = reaction

# matches should be list of list (list of tokens
# [['this'], ['this', 'or', 'that']]
def eat(matches, tokens):
    for match_tokens in matches:
        equal = True
        for i in range(len(match_tokens)):
            if i >= len(tokens) or match_tokens[i] != tokens[i]:
                equal = False
                break;
        if equal:
            for i in range(len(match_tokens)):
                tokens.pop(0)
            return match_tokens

class Objects:
    def __init__(self):
        self.objects = []
        
    def add(self, name, description, actions):
        self.objects.append(Object(name, description, actions))

    def get(self, name):
        matches = list(filter(lambda x: x.name == x, self.objects))
        if len(matches) > 1:
            raise Exception('More than one object named "%s"' % name)
        elif len(matches) < 1:
            raise Exception("Couldn't find object with name \"%s\"" % name)
        return matches[0]

    def eat(self, tokens):
        match_tokens = eat(map(lambda x: x.tokenize(), self.enumerate()), tokens)
        return ' '.join(match_tokens) if match_tokens else None
    
    def enumerate(self):
        return sorted(self.objects, key=lambda x: len(x.name), reverse=True)

    def on(self, object_name, action_name, reaction):
        self.get(object_name).on(action_name, reaction)
        
class Actions:
    def __init__(self, skip_words=None):
        self.actions = []
        self.skip_words = skip_words if skip_words else []

    def add(self, name, *aliases):
        self.actions.append(list(map(str.split, [name] + list(aliases))))

    def add_skip_words(self, *skip_words):
        self.skip_words += skip_words

    def eat(self, tokens):
        actions = self.enumerate()
        for action in actions:
            cursor = 0
            skip_words = 0
            ate = True
            while ate:
                ate = False

                if cursor + skip_words >= len(tokens):
                    break;
                if tokens[cursor + skip_words] in self.skip_words:
                    skip_words += 1
                    ate = True
                    continue;

                if cursor >= len(action):
                    break
                if action[cursor] == tokens[cursor + skip_words]:
                    cursor += 1
                    ate = True
            if cursor == len(action):
                for x in range(cursor + skip_words):
                    tokens.pop(0)
                return self.canonicalize(action)

    def enumerate(self):
        all_actions = []
        for action in self.actions:
            for alias in action:
                all_actions.append(alias)
        return sorted(all_actions, key=len, reverse=True)
    
    def canonicalize(self, name):
        if type(name) == str:
            name = name.split(' ')
        for action in self.actions:
            if name in action:
                return ' '.join(action[0])

class Game:
    def __init__(self, char, rooms, objs, acts, dirs):
        self.char = char
        self.rooms = rooms
        self.objs = objs
        self.acts = acts
        self.dirs = dirs

        self.go_action_name = 'go'
        self.look_action_name = 'look'        

    def set_go_action_name(self, action_name):
        self.go_action_name = action_name

    def set_look_action_name(self, action_name):
        self.look_action_name = action_name
        
    def go(self, direction):
        '''
        Moves the character to a room in this direction
        '''
        next_room = self.rooms.go(self.char.room, direction)
        if not next_room:
            print('You cannot go %s' % direction)
        else:
            print(self.rooms.get(next_room).description)
            self.char.room = next_room

    def exec(self, string):
        tokens = re.split('\s+', string.strip())
        
        action = self.acts.eat(tokens)
        object = self.objs.eat(tokens)
        direction = self.dirs.eat(tokens)

        if action == self.go_action_name:
            if not direction:
                print('You must give a valid direction to go')
            else:
                self.go(direction)
        elif action == self.look_action_name:
            print(self.rooms.get(self.char.room).description)
            adjacent_rooms = self.rooms.get_adjacent_rooms(self.char.room)
            for direction in adjacent_rooms:
                print('A %s is to the %s' % (adjacent_rooms[direction], direction))
                
class Room:
    def __init__(self, name, description='', objects=None):
        self.name = name
        self.description = description
        self.objects = objects if objects != None else []
        self.connections = []

class Rooms:
    def __init__(self):
        self.mappings = {}
        self.rooms = {}

    def add(self, name, description, objects=None, connections=None):
        self.rooms[name] = Room(name, description, objects)
        
    def map(self, from_room, direction, to_room, bidirectional=True):
        if from_room not in self.mappings:
            self.mappings[from_room] = []
        if to_room not in self.mappings:
            self.mappings[to_room] = []
            
        self.mappings[from_room].append((direction, to_room))
        
        if bidirectional:
            self.mappings[to_room].append((direction, from_room))

    def get(self, room_name):
        return self.rooms[room_name]

    def get_adjacent_rooms(self, room_name):
        return dict(self.mappings[room_name])
    
    def go(self, from_room, direction):
        for (direction, to_room) in self.mappings[from_room]:
            if direction == direction:
                return to_room
            
class Directions:
    def __init__(self):
        self.directions = []
        self.opposites = {}

    def add(self, name, *aliases):
        self.directions.append([name] + list(aliases))

    def canonicalize(self, name):
        for direction in self.directions:
            if name in direction:
                return direction[0]

    def enumerate(self):
        all_directions = []
        for direction in self.directions:
            for alias in direction:
                all_directions.append(alias)
        return sorted(all_directions, key=len, reverse=True)

    def eat(self, tokens):
        match_tokens = eat(map(lambda x: x.split(' '), self.enumerate()), tokens)
        return ' '.join(match_tokens) if match_tokens else None
    
    def add_opposite(self, name, opposite_name):
        name = self.canonicalize(name)
        opposite_name = self.canonicalize(opposite_name)
        self.opposites[name] = opposite_name
        self.opposites[opposite_name] = name

    def get_opposite(self, name):
        name = self.canonicalize(name)
        return self.opposites[name]
