import inspect
import enum
import sys

class ParamParserType(enum.Enum):
    SPACES = 'SPACES'
    ALL = 'ALL'
    CUSTOM = 'CUSTOM'

class CommandRegistry():
    # Command dictionary keys
    NUM_PARAMS = 'numParams'
    PARAM_NAMES = 'paramNames'
    DESCRIPTION = 'description'
    COMMAND_NAME = 'name'
    FUNCTION_NAME = 'funcName'
    OVERRIDE_DEFAULT_PARSER = 'overrideDefaultParser'
    PARAM_PARSER = 'paramParser'
    PARAM_PARSER_TYPE = 'paramParserType'
    USAGE = 'usage'
    
    PARAM_PARSER_SPACES = lambda args: [] if args.split(' ') == [''] else args.split(' ')
    PARAM_PARSER_ALL = lambda args: args

    def __init__(self):
        self.registry = {}

class CommandHelper:
    # Gets the help information for the commands provided in a nicely formatted string
    # Format 1 (bot commands):    !<commandname> <parameters>  - <description>
    # Format 2 (plugin commands): !<tag> <commandname> <parameters>  - <description>
    # example 1: !file save <url> <name>  - Saves the file at <url> to a local file named <name>
    # example 2: !hello  - Say Hello
    # @param commandList    The list of commands 
    # @param tag            The plugin's tag (optional)
    # @return  An array of help strings
    def _getCommandHelp(commandList, tag = None):
        commands = []
        overloads = {}

        for key, value in commandList.items():
            numOverloads = len(value[CommandRegistry.FUNCTION_NAME])

            for i in range(numOverloads):
                if tag is not None:
                    str = '`!{} {} '.format(tag, key)
                else:
                    str = '`!{} '.format(key)
                
                if numOverloads > 1:
                    overloads[key] = numOverloads
        
                if len(value[CommandRegistry.PARAM_NAMES][i]) != 0:
                    for paramName in value[CommandRegistry.PARAM_NAMES][i]:
                        str += '<{}> '.format(paramName)

                str += '`  - {}'.format(value[CommandRegistry.DESCRIPTION][i])
                commands.append(str)

        # Sort the commands
        commands = sorted(commands)

        commandPrefix = '!' + (tag + ' ') if tag is not None else ''

        for key, value in overloads.items():
            index = next(i for i, item in enumerate(commands) if commandPrefix + key in item)

            commands[index:index+value] = sorted(commands[index:index+value], key=lambda com: com.count('<'))

        return commands

    # Checks if the command provided by the user is handled 
    # @param commandList        The list of commands 
    # @param command            The command the user wants to execute
    # @return                   Returns False if it can't handle it, True if it can
    def _isCommand(commandList, command):
        return (True if command in commandList else False)

    # Parses the args based on the command's settings
    # @param commandList        The list of commands 
    # @param command            The command the user wants to execute
    # @param args               The remaining text, which will be parsed into args for execution
    # @param defaultParser      The default parser to use on the args if an override isn't given
    # @param defaultParserType  The type of the default parser
    # @param logger             The logger to use (not required)
    # @return                   Returns the parsed args in an array
    def _parseCommandArgs(commandList, command, args, defaultParser, defaultParserType, logger = None):
        if command in commandList:
            cmd = commandList[command]

            numParams = cmd[CommandRegistry.NUM_PARAMS]
            temp = defaultParser(args)
            parserType = defaultParserType 
                
            if cmd[CommandRegistry.OVERRIDE_DEFAULT_PARSER] == True:
                temp = cmd[CommandRegistry.PARAM_PARSER](args)
                parserType = cmd[CommandRegistry.PARAM_PARSER_TYPE]

            if logger is not None:
                logger.debug('Command [%s] Parsed', command)
                logger.debug('ParserType: %s', parserType)

            # Break out early if we want all the arguments as a parameter
            if len(numParams) == 1 and parserType == ParamParserType.ALL:
                if logger is not None: logger.debug('Args: [%s]', temp)
                return 0, [temp]

            # Determine which function to call based on the number of parameters
            numParsedParams = len(temp)
            index = -1

            for i, item in enumerate(numParams):
                if item == numParsedParams:
                    index = i
                    break

            if index != -1:
                num = int(numParams[index])
                # Break out early if no params
                if num == 0:
                    if logger is not None: logger.debug('Args: []')
                    return index, []

                if logger is not None: logger.debug('Args: %s', temp[:num])
                return index, temp[:num]

        return -1, [] 

    # Executes the command
    # @param obj            The object that has the function for the command being called
    # @param commandList    The list of commands
    # @param args           Any extra parameters that followed the command
    # @param logger         The logger to use (not required)
    # @param kwargs         The information for the command
    async def _executeCommand(obj, commandList, index, args, logger = None, **kwargs):
        command = kwargs.pop('command')

        if index == -1 or index >= len(commandList[command][CommandRegistry.NUM_PARAMS]):
            if logger is not None: logger.error('The index (%i) provided is invalid.', index)

        num = commandList[command][CommandRegistry.NUM_PARAMS][index]
        paramNames = commandList[command][CommandRegistry.PARAM_NAMES][index]
        funcName = commandList[command][CommandRegistry.FUNCTION_NAME][index]

        if len(args) != len(paramNames):
            if logger is not None: logger.error('The number of arguments (%s) and the number of parameter names (%s) does not match!', len(args), len(paramNames))

        for i, name in enumerate(paramNames):
            kwargs[name] = args[i]

        if logger is not None: logger.debug('Executing command [%s] with arguments [%s]', command, str(args)[1:-1])
        await getattr(obj, funcName)(**kwargs)

    def _trim_docstring(docstring):	
        if not docstring:
            return ''

        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
        lines = docstring.expandtabs().splitlines()

        # Determine minimum indentation (first line doesn't count):
        indent = sys.maxsize
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:
                indent = min(indent, len(line) - len(stripped))

        # Remove indentation (first line is special):
        trimmed = [lines[0].strip()]
        if indent < sys.maxsize:
            for line in lines[1:]:
                trimmed.append(line[indent:].rstrip())

        # Strip off trailing and leading blank lines:
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)

        # Return a single string:
        return '\n'.join(trimmed)

# Reference for auto registering decorated functions for a class
# http://stackoverflow.com/questions/3054372/auto-register-class-methods-using-decorator
# I should explore this and see if I can use it

# Reference for auto registering decorated functions
# http://stackoverflow.com/questions/5707589/calling-functions-by-array-index-in-python/5707605#5707605

def _loadCommands():
    def commandRegistrar(description, **kwargs):
        def decorator(func):
            className = func.__qualname__.split('.', 1)[0]
            funcName = func.__name__
            commandName = kwargs[CommandRegistry.COMMAND_NAME] if CommandRegistry.COMMAND_NAME in kwargs else funcName
            usage = CommandHelper._trim_docstring(func.__doc__)
            params = []

            for i, key in enumerate(inspect.signature(func).parameters):
                # remove things that are not important
                if key is not 'self' and key is not 'server' and \
                   key is not 'channel' and key is not 'author' and \
                   key is not 'kwargs':
                    params.append(key)

            #print('Class Name:', className)
            #print('Command Name:', commandName)
            #print('Func Name:', funcName)
            #print('Params:', params)
            #if 'parser' in kwargs: print('Parser:', kwargs['parser'])
            #if 'parserType' in kwargs: print('Parser Type:', kwargs['parserType'])

            if className not in commandRegistry.registry:
                commandRegistry.registry[className] = {}

            if commandName not in commandRegistry.registry[className]:
                commandRegistry.registry[className][commandName] = {}

            if CommandRegistry.FUNCTION_NAME not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.FUNCTION_NAME] = []

            if CommandRegistry.NUM_PARAMS not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.NUM_PARAMS] = []

            if CommandRegistry.PARAM_NAMES not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.PARAM_NAMES] = []

            if CommandRegistry.DESCRIPTION not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.DESCRIPTION] = []

            if CommandRegistry.USAGE not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.USAGE] = []

            if CommandRegistry.PARAM_PARSER_TYPE not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER_TYPE] = ParamParserType.SPACES
                commandRegistry.registry[className][commandName][CommandRegistry.OVERRIDE_DEFAULT_PARSER] = False

            if CommandRegistry.PARAM_PARSER not in commandRegistry.registry[className][commandName]:
                commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER] = CommandRegistry.PARAM_PARSER_SPACES

            commandRegistry.registry[className][commandName][CommandRegistry.FUNCTION_NAME].append(funcName)
            commandRegistry.registry[className][commandName][CommandRegistry.NUM_PARAMS].append(len(params))
            commandRegistry.registry[className][commandName][CommandRegistry.PARAM_NAMES].append(params)
            commandRegistry.registry[className][commandName][CommandRegistry.DESCRIPTION].append(description)
            commandRegistry.registry[className][commandName][CommandRegistry.USAGE].append(usage)

            if 'parser' in kwargs:
                commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER] = kwargs['parser']
                commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER_TYPE] = ParamParserType.CUSTOM
                commandRegistry.registry[className][commandName][CommandRegistry.OVERRIDE_DEFAULT_PARSER] = True
            elif 'parserType' in kwargs:
                isValid = lambda enumVal: True if enumVal in ParamParserType and enumVal != ParamParserType.CUSTOM else False

                if isValid(kwargs['parserType']):
                    commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER_TYPE] = kwargs['parserType']
                    commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER] = getattr(CommandRegistry, 'PARAM_PARSER_' + kwargs['parserType'].name)
                    commandRegistry.registry[className][commandName][CommandRegistry.OVERRIDE_DEFAULT_PARSER] = True

            #print('Registry Parser:', commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER])
            #print('Registry Parser Type:', commandRegistry.registry[className][commandName][CommandRegistry.PARAM_PARSER_TYPE])

            return func
        return decorator

    commandRegistrar.registry = commandRegistry.registry
    return commandRegistrar

commandRegistry = CommandRegistry()

