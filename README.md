# py2mint

Python tools for mint creation, manipulation, and application.

## What's mint?

Mint stands for "Meta-INTerface".

Minting is core technique of i2i: It can be seen as the encapsulation of a construct’s interface into a (data) 
structure that contains everything one needs to know about the construct to perform a specific action 
with or on the construct.

A little note on the use of “encapsulation”. The term is widely used in computer science, 
and is typically tied to object oriented programming. Wikipedia provides two definitions:
* A language mechanism for restricting direct access to some of the object's components.
* A language construct that facilitates the bundling of data with the methods (or other functions) 
operating on that data.

Though both these definitions apply to minting, 
the original sense of the word “encapsulate” is even more relevant (from google definitions): 
* express the essential features of (something) succinctly
* enclose (something) in or as if in a capsule

Indeed, minting is the process of enclosing a construct into a “mint” (for “Meta INTerface”) 
that will express the features of the construct that are essential to the task at hand. 
The mint provides a declarative layer of the construct that allows one to write code that operates with this layer, 
which is designed to be (as) consistent (as possible) from one system/language to another.

For example, whether a (non-anonymous) function was written in C, Python, or JavaScript, 
it will at least have a name, and it’s arguments will (most often) have names, and may have types. 
Similarly with “data objects”: The data of both JavaScript and Python objects can be represented by a tree whose 
leaves are base types, which can in turn be represented by a C struct. 

