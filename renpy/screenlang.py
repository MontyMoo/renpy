# Copyright 2004-2010 PyTom <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import renpy

##############################################################################
# Data types.

class InvalidType(Exception):
    """
    An exception that is thrown when we can't parse an object of
    the expected type.
    """

# Sentinel type used for classes that do not have a default type.
NoDefault = object()

class Type(renpy.object.Object):
    """
    Base class for types.
    """

    default = NoDefault

    def __init__(self, l):

        try:
            self.state = self.parse(l)
        except renpy.parser.ParseError:
            if self.default:
                self.state = self.default
            else:
                raise
                
    def parse(self, l):
        """
        The parse method is responsible for parsing an expression of the given
        type. It returns some state, or raises InvalidType if it can't.
        """

        # Since most of the types are really wrappers around simple_expression,
        # we default to that.
        return l.require(l.simple_expression)
            

    def evaluate(self, state, scope):
        """
        This is called at runtime with the result of parse, and is
        responsible for returning an actual value. It can also raise
        InvalidType if the expression does not return the appropriate
        type.
        """

        raise NotImplemented

    def get_value(self, scope):
        return self.evaluate(self.state, scope)

class Name(Type):
    def parse(self, l):
        return l.require(l.name)

    def evaluate(self, state, scope):
        return state

class ImageName(Type):
    def parse(self, l):
        rv = [ ]

        rv.append(l.require(l.name))

        while True:
            n = l.name()
            if n is None:
                break

            rv.append(n)
        
        return tuple(rv)

    def evaluate(self, state, scope):
        return state
    
class Expression(Type):
    def evaluate(self, state, scope):
        return eval(state, renpy.store.__dict__, scope)
    
    
##############################################################################
# Parsing.

# The parser that things are being added to.
parser = None

class Positional(object):
    """
    This represents a positional parameter to a function.
    """

    def __init__(self, name, type=Expression, help=None):
        self.name = name
        self.type = type
        self.help = help

        if parser:
            parser.add(self)
        
class Keyword(object):
    """
    This represents an optional keyword parameter to a function.
    """
    
    def __init__(self, name, type=Expression, help=None):
        self.name = name
        self.type = type
        self.help = help
        self.style = False

        if parser:
            parser.add(self)
        
class Style(object):
    """
    This represents a style parameter to a function.
    """

    def __init__(self, name, type=Expression, help=None):
        self.name = name
        self.type = type
        self.help = help
        self.style = True

        if parser:
            parser.add(self)


class Parser(object):

    def __init__(self, name):

        # The name of this object.
        self.name = name
        
        # The positional arguments, keyword arguments, and child
        # statements of this statement.
        self.positional = [ ]
        self.keyword = { }
        self.children = { }

        all_statements.append(self)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def add(self, i):
        """
        Adds a clause to this parser.
        """

        if isinstance(i, list):
            for j in i:
                self.add(j)

            return
        
        if isinstance(i, Positional):
            self.positional.append(i)

        elif isinstance(i, Keyword):
            self.keyword[i.name] = i                

        elif isinstance(i, Style):
            for j in renpy.style.prefix_subs:
                self.keyword[j + i.name] = i

        elif isinstance(i, Parser):
            self.children[i.name] = i

    def parse_statement(self, l):
        word = l.word()
        if word and word in self.children:
            c = self.children[word].parse(l)
            return c
        else:            
            return None
        
            
# A singleton value.
many = object()
    
class FunctionStatementParser(Parser):
    """
    This is responsible for parsing function statements.
    """

    def __init__(self, name, function, nchildren=0, unevaluated=False):

        super(FunctionStatementParser, self).__init__(name)
        
        # Functions that are called when this statement runs.
        self.function = function

        # The number of children we have.
        self.nchildren = nchildren
        
        # True if we should evaluate arguments and children. False
        # if we should just pass them into our child.
        self.unevaluated = unevaluated

        # Add us to the appropriate lists.
        global parser
        parser = self

        if nchildren != 0:
            childbearing_statements.append(self)
            
    def parse(self, l):
        """
        Parses this statement (and the associated block) into a
        FunctionStatement object.
        """

        # These are used to store the various arguments as they come in.        
        positional = [ ]
        keyword = { }
        children = [ ]

        # Parses a keyword argument from the lexer.
        def parse_keyword(l):
            name = l.word()

            if not Name:
                l.error('expected a keyword argument, colon, or end of line.')
            
            if name not in self.keyword:
                l.error('%r is not a keyword argument or valid child for the %s statement.' % (name, self.name))
            
            if name in keyword:
                l.error('keyword argument %r appears more than once in a %s statement.' % (name, self.name))

            keyword[name] = self.keyword[name].type(l)
        
        # We assume that the initial keyword has been parsed already,
        # so we start with the positional arguments.

        for i in self.positional:
            positional.append(i.type(l))

        # Next, we allow keyword arguments on the starting line.
        while True:
            if l.match(':'):
                l.expect_eol()
                l.expect_block(self.name)
                block = True
                break

            if l.eol():
                l.expect_noblock(self.name)
                block = False
                break

            parse_keyword(l)

        # If we have a block, then parse each line.
        if block:

            l = l.subblock_lexer()

            while l.advance():

                state = l.checkpoint()

                c = self.parse_statement(l)
                if c is not None:
                    children.append(c)
                    continue
                
                l.revert(state)

                while not l.eol():
                    parse_keyword(l)

        return FunctionStatement(self.function, self.nchildren, positional, keyword, children, self.unevaluated)

class FunctionStatement(renpy.object.Object):
    def __init__(self, function, nchildren, positional, keyword, children, unevaluated):
        self.function = function
        self.nchildren = nchildren
        self.positional = positional
        self.keyword = keyword
        self.children = children
        self.unevaluated = unevaluated

                
    def evaluate(self, name, scope):

        if self.unevaluated:
            return self.function(self.positional, self.keyword, self.children)
                
        positional = [ i.get_value(scope) for i in self.positional ]
        keyword = dict((k, v.get_value(scope)) for k, v in self.keyword.iteritems())

        if "id" not in keyword:
            keyword["id"] = name
            
        rv = self.function(*positional, **keyword)

        if self.nchildren == 1:
            renpy.ui.child_or_fixed()

        for i, child in enumerate(self.children):
            child.evaluate(name + (i, ), scope)

        if self.nchildren != 0:
            renpy.ui.close() 
            
        return rv
        

##############################################################################
# Definitions of screen language statements.

# Used to allow statements to take styles.
styles = [ ]

# All statements defined, and statements that take children.
all_statements = [ ]
childbearing_statements = [ ]

position_properties = [ Style(i, Expression) for i in [
        "anchor",
        "xanchor",
        "yanchor",
        "pos",
        "xpos",
        "ypos",
        "align",
        "xalign",
        "yalign",
        "xoffset",
        "yoffset",
        "area",
        ] ]

text_properties = [ Style(i, Expression) for i in [
        "antialias",
        "black_color",
        "bold",
        "color",
        "drop_shadow",
        "drop_shadow_color",
        "first_indent",
        "font",
        "size",
        "italic",
        "justify",
        "language",
        "layout",
        "line_spacing",
        "minwidth",
        "min_width",
        "outlines",
        "rest_indent",
        "slow_cps",
        "slow_cps_multiplier",
        "slow_abortable",
        "text_align",
        "text_y_fudge",
        "underline",
        "xmaximum",
        "ymaximum",
        "xminimum",
        "yminimum",
        "xfill",
        "yfill",
        "clipping",
        ] ]

window_properties = [ Style(i, Expression) for i in [
        "background",
        "foreground",
        "left_margin",
        "right_margin",
        "bottom_margin",
        "top_margin",
        "xmargin",
        "ymargin",
        "left_padding",
        "right_padding",
        "top_padding",
        "bottom_padding",
        "xpadding",
        "ypadding",
        "side_group",
        ] ]

button_properties = [ Style(i, Expression) for i in [
        "sound",
        "focus_mask",
        "focus_rect",
        "time_policy",
        "child",
        "mouse",
        ] ]

bar_properties = [ Style(i, Expression) for i in [
        "bar_vertical",
        "bar_invert"
        "bar_resizing",
        "left_gutter",
        "right_gutter",
        "top_gutter",
        "bottom_gutter",
        "left_bar",
        "right_bar",
        "top_bar",
        "bottom_bar",
        "thumb",
        "thumb_shadow",
        "unscrollable",
        ] ]

box_properties = [ Style(i, Expression) for i in [
        "box_layout",
        "spacing",
        "first_spacing",
        ] ]

ui_properties = [
    Keyword("at"),
    Keyword("id"),
    Keyword("style"),
    ]


def add(thing):
    parser.add(thing)


    
##############################################################################
# UI statements.

FunctionStatementParser("null", renpy.ui.null, many)
Keyword("width")
Keyword("height")
add(ui_properties)
add(position_properties)


FunctionStatementParser("text", renpy.ui.text, 0)
Positional("text")
Keyword("slow")
add(ui_properties)
add(position_properties)
add(text_properties)

FunctionStatementParser("hbox", renpy.ui.hbox, many)
add(ui_properties)
add(position_properties)
add(box_properties)

FunctionStatementParser("vbox", renpy.ui.vbox, many)
add(ui_properties)
add(position_properties)
add(box_properties)

FunctionStatementParser("fixed", renpy.ui.fixed, many)
add(ui_properties)
add(position_properties)
add(box_properties)

FunctionStatementParser("grid", renpy.ui.grid, many)
Positional("cols")
Positional("rows")
Keyword("transpose")
add(ui_properties)
add(position_properties)
add(box_properties)

FunctionStatementParser("side", renpy.ui.side, many)
Positional("positions")
add(ui_properties)
add(position_properties)
add(box_properties)

# Omit sizer, as we can always just put an xmaximum and ymaximum on an item.

for name in [ "window", "frame" ]:
    FunctionStatementParser(name, getattr(renpy.ui, name), 1)
    add(ui_properties)
    add(position_properties)
    add(window_properties)

# Omit keymap in favor of key.
# Omit behaviors.
# Omit menu as being too high-level.

FunctionStatementParser("input", renpy.ui.input, 0)
Positional("default")
Keyword("length")
Keyword("allow")
Keyword("exclude")
Keyword("prefix")
Keyword("suffix")
Keyword("changed")
add(ui_properties)
add(position_properties)
add(button_properties)

FunctionStatementParser("add", renpy.ui.image, 0)
Positional("im")

FunctionStatementParser("image", renpy.ui.image, 0)
Positional("im")

# Omit imagemap_compat for being too high level (and obsolete).

FunctionStatementParser("button", renpy.ui.button, 1)
Keyword("clicked")
Keyword("hovered")
Keyword("unhovered")
add(ui_properties)
add(position_properties)
add(window_properties)
add(button_properties)

FunctionStatementParser("imagebutton", renpy.ui.imagebutton, 0)
Keyword("auto")
Keyword("idle")
Keyword("hover")
Keyword("insensitive")
Keyword("selected_idle")
Keyword("selected_hover")
Keyword("selected_insensitive")
Keyword("clicked")
Keyword("hovered")
Keyword("unhovered")
Keyword("image_style")
add(ui_properties)
add(position_properties)
add(window_properties)
add(button_properties)

FunctionStatementParser("textbutton", renpy.ui.textbutton, 0)
Positional("label")
Keyword("clicked")
Keyword("hovered")
Keyword("unhovered")
Keyword("text_style")
add(ui_properties)
add(position_properties)
add(window_properties)
add(button_properties)

for name in [ "bar", "vbar", "slider", "vslider", "scrollbar", "vscrollbar" ]:
    FunctionStatementParser(name, getattr(renpy.ui, name), 0)    
    Keyword("adjustment")
    add(ui_properties)
    add(position_properties)
    add(bar_properties)
    
# Omit autobar. (behavior)
# Omit transform. (replaced by at)

FunctionStatementParser("viewport", renpy.ui.viewport, 1)
Keyword("child_size")
Keyword("mousewheel")
Keyword("draggable")
add(ui_properties)
add(position_properties)

# Omit conditional. (behavior)
# Omit timer. (behavior)

FunctionStatementParser("imagemap", renpy.ui.imagemap, many)
Keyword("ground")
Keyword("hover")
Keyword("insensitive")
Keyword("idle")
Keyword("selected_hover")
Keyword("selected_idle")
Keyword("auto")
add(ui_properties)
add(position_properties)

FunctionStatementParser("hotspot", renpy.ui.hotspot, 1)
Positional("spot")
Keyword("clicked")
Keyword("hovered")
Keyword("unhovered")
add(ui_properties)
add(position_properties)
add(button_properties)

FunctionStatementParser("hotbar", renpy.ui.hotbar, 0)
Positional("spot")
Keyword("adjustment")
add(ui_properties)
add(position_properties)
add(bar_properties)

# TODO: need to add the key statement.
    
##############################################################################
# Control-flow statements.

def pass_function():
    pass

FunctionStatementParser("pass", pass_function, 0)


class IncludeParser(Parser):

    def __init__(self, name):
        super(IncludeParser, self).__init__(name)
        childbearing_statements.append(self)
        
    def parse(self, l):

        name = ( l.require(l.name), )

        while True:
            n = l.name()
            if n is None:
                break

            name = name + (n, )

        args = renpy.parser.parse_arguments(l)

        for k, v in args.arguments:
            if k is None:
                l.error('The include statement only takes keyword arguments.')

        if args.extrapos:
            l.error('The include statement only takes keyword arguments.')

        return Include(name, args)

class Include(renpy.object.Object):

    def __init__(self, screen, args):
        self.screen = screen
        self.args = args

    def evaluate(self, name, scope):

        kwargs = { }
        
        # Args are optional.
        if self.args:

            if self.args.extrakw:
                kwargs = eval(self.args.extrakw, renpy.store.__dict__, scope)
                
            for k, v in self.args.arguments:
                kwargs[k] = eval(v, renpy.store.__dict__, scope)

        renpy.display.screen.include_screen(self.screen, _name=name, **kwargs)

IncludeParser("include")
        

##############################################################################
# Add all_statements to the statements that take children.

for i in childbearing_statements:
    i.add(all_statements)

##############################################################################
# Definition of the screen statement.

class ScreenFunction(renpy.object.Object):

    def __init__(self, children):
        self.children = children

    def __call__(self, _name=(), _scope=None, **kwargs):

        for i, child in enumerate(self.children):
            child.evaluate(_name + (i,), _scope)
    
def screen_function(positional, keyword, children):
    scope = { }

    name = positional[0].get_value(scope)

    if "modal" in keyword:
        modal = keyword.pop("modal").get_value(scope)
    else:
        modal = True

    if "layer" in keyword:
        layer = keyword.pop("modal").get_value(scope)
    else:
        layer = 'screens'

    function = ScreenFunction(children)
    
    return {
        "name" : name,
        "function" : function,
        "modal" : modal,
        "layer" : layer,
        }
    
screen_stmt = FunctionStatementParser("screen", screen_function, unevaluated=True)
Positional("name", ImageName)
Keyword("modal", Expression)
Keyword("layer", Expression)
add(all_statements)

def parse_screen(l):
    """
    Parses the screen statement.
    """

    return screen_stmt.parse(l).evaluate((), {})
    
        