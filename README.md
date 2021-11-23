# Lab_ImageJ_Wellplate_MultiMeasure
Python-based ImageJ macro

Existing Java-based macro was produced by Ross Lagoy and Dan Lawler
Java-based code measured one set of positions (animals) for all the videos of a given well

This code was an exercise in using Python as an ImageJ macro, adding support for the video-specific
position sets that can be produced with the MATLAB code Lab_Neuron_Position_GUI.

Initial testing on 11/5/2021 showed this code producing the same output as the established 
java-based macro, given the same inputs (2 wells of images and 'static' positions)

Future updates could include making frame-specific position sets, and measurement boxes of varied size
