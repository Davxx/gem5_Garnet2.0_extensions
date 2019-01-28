**Author**: David Smelt
**Date**: June 23, 2018

# This is a fork of the gem5 simulator (c) (forked <a href="https://github.com/gem5/gem5/commit/5187a24d496cd16bfe440f52ff0c45ab0e185306" target="_blank">April 27, 2018</a>) with Garnet2.0 extensions.
It provides an easy framework for running and evaluating Garnet2.0 simulations.
The extensions were built to aid in my computer science bachelor's thesis: <a href="https://github.com/Davxx/gem5_Garnet2.0_extensions/raw/master/doc/Thesis%20-%20David%20Smelt%20-%20Modeling%20many-core%20processor%20interconnect%20scalability%20for%20the%20evolving%20performance%2C%20power%20and%20area%20relation.pdf" target="_blank">Modeling many-core processor interconnect scalability for the evolving performance, power and area relation</a>.

**Please refer to <a href="https://github.com/Davxx/gem5_Garnet2.0_extensions/raw/master/doc/thesis_excerpt_garnet2.0_extensions.pdf" target="_blank">doc/thesis_excerpt_garnet2.0_extensions.pdf</a> for documentation.**

**Important notes**:
   - util/on-chip-network-power-area-2.0.py features an updated integration of DSENT with Garnet2.0.
     - It relies heavily on other extensions, e.g.:
     - Edit configs/topologies/TopologyToDSENT.py to modify the generated DSENT router.cfg and electrical-link.cfg files.
   - FlattenedButterfly lacks the canonically proposed repeaters and pipeline registers for links connecting non-neighboring routers.
     - However, DSENT can insert repeaters on-the-fly.
   - Ring and HierarchicalRing lack a deadlock escape algorithm.
   - HierarchicalRing lacks microarchitectural differentiation between the central ring and any of the sub-rings.
   - sniper_splash2/splash2/codes/kernels/fft/FFT is still deficient: more cores effectuate higher execution times. One is best served selecting a more approriate benchmark for comparing gem5 SE/FS-mode interconnect performance.
   - No updates are planned as of June 24, 2018.
   - Use the extensions as you please; no warranty is provided.

<hr>

# gem5 is copyrighted software
> Please see individual files for details of the license on each file.
> The preferred license can be found in LICENSE.
> 
> All files in this distribution (other than in the ext directory) have
> licenses based on the BSD or MIT licenses.  Some files in the ext
> directory are GNU LGPL.  No other licenses are found in this
> distribution.
> 
> Beyond the BSD license, some files include the following clarification
> of the license as required by the copyright holder:
> 
>     The license below extends only to copyright in the software and
>     shall not be construed as granting a license to any other
>     intellectual property including but not limited to intellectual
>     property relating to a hardware implementation of the
>     functionality of the software licensed hereunder.  You may use the
>     software subject to the license terms below provided that you
>     ensure that this notice is replicated unmodified and in its
>     entirety in all distributions of the software, modified or
>     unmodified, in source code or in binary form.
> 
> The copyright holders include (not counting the ext directory):
> 
> Copyright (c) 2000-2011 The Regents of The University of Michigan
> Copyright (c) 1990,1993-1995,2007-2010 The Hewlett-Packard Development Company
> Copyright (c) 1999-2009,2011 Mark D. Hill and David A. Wood
> Copyright (c) 2009-2011 ARM Limited
> Copyright (c) 2008-2009 Princeton University
> Copyright (c) 2007 MIPS Technologies, Inc.
> Copyright (c) 2009-2011 Advanced Micro Devices, Inc.
> Copyright (c) 2009 The University of Edinburgh
> Copyright (c) 2007-2008 The Florida State University
> Copyright (c) 2010 Massachusetts Institute of Technology
> Copyright (c) 1990-1993 The Regents of the University of California
> Copyright (c) 2006-2009 Nathan Binkert
> Copyright (c) 2001 The NetBSD Foundation, Inc.
> Copyright (c) 2010-2011 Gabe Black
> Copyright (c) 1994 Adam Glass
> Copyright (c) 1990-1992 MIPS Computer Systems, Inc.
> Copyright (c) 2004 Richard J. Wagner
> Copyright (c) 2000 Computer Engineering and Communication Networks Lab
> Copyright (c) 2001 Eric Jackson
> Copyright (c) 1990 Hewlett-Packard Development Company
> Copyright (c) 1994-1996 Carnegie-Mellon University.
> Copyright (c) 1993-1994 Christopher G. Demetriou
> Copyright (c) 1997-2002 Makoto Matsumoto and Takuji Nishimura
> Copyright (c) 1998,2001 Manuel Bouyer.
> Copyright (c) 2016-2017 Google Inc.


# Original gem5 README
This is the gem5 simulator.

The main website can be found at http://www.gem5.org

A good starting point is http://www.gem5.org/Introduction, and for
more information about building the simulator and getting started
please see http://www.gem5.org/Documentation and
http://www.gem5.org/Tutorials.

To build gem5, you will need the following software: g++ or clang,
Python (gem5 links in the Python interpreter), SCons, SWIG, zlib, m4,
and lastly protobuf if you want trace capture and playback
support. Please see http://www.gem5.org/Dependencies for more details
concerning the minimum versions of the aforementioned tools.

Once you have all dependencies resolved, type 'scons
build/<ARCH>/gem5.opt' where ARCH is one of ALPHA, ARM, NULL, MIPS,
POWER, SPARC, or X86. This will build an optimized version of the gem5
binary (gem5.opt) for the the specified architecture. See
http://www.gem5.org/Build_System for more details and options.

With the simulator built, have a look at
http://www.gem5.org/Running_gem5 for more information on how to use
gem5.

The basic source release includes these subdirectories:
   - configs: example simulation configuration scripts
   - ext: less-common external packages needed to build gem5
   - src: source code of the gem5 simulator
   - system: source for some optional system software for simulated systems
   - tests: regression tests
   - util: useful utility programs and files

To run full-system simulations, you will need compiled system firmware
(console and PALcode for Alpha), kernel binaries and one or more disk
images. Please see the gem5 download page for these items at
http://www.gem5.org/Download

If you have questions, please send mail to gem5-users@gem5.org

Enjoy using gem5 and please share your modifications and extensions.
