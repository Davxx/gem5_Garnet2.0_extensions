# Author: David Smelt

import os
import subprocess

# Class for generating Tikz topology code,
# will be written to 'sim_output_directory/topo.tex'
# If imagemagick is installed, the topology is written to 'sim_output_directory/topology.png'

class TikzTopology():
    def __init__(self, nrows, ncols):
        # Use different base names for texname and pngname
        self.texname = "topo.tex"
        self.pngname = "topology.png"
        
        # Remove tex files after successful PNG generation
        self.cleanup = False 

        self.tikzfile = None
        self.outdir = os.environ["GEM5OUTDIR"] if "GEM5OUTDIR" in os.environ else "m5out"

        # Create output dir if it does not exist yet
        if not os.path.isdir(self.outdir):
            os.makedirs(self.outdir)

        try:
            width = ncols * 0.8 if ncols == nrows else ncols * 1.2
            height = nrows * 0.8 if ncols == nrows else nrows * 1.2
            self.tikzfile = open(os.path.join(self.outdir, self.texname), "w")
            self.tikzfile.write("\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage{tikz}\n"
                                "\\usepackage[letterpaper,paperwidth=" + str(int(width)) + "in,paperheight="\
                                + str(int(height)) + "in]{geometry}\n\\geometry{margin=0.3in}\n\\usepackage{float}\n"
                                "\\begin{document}\n\\pagenumbering{gobble}\n\\begin{figure}[p]\n\\centering\n"
                                "\\begin{tikzpicture}[shorten >=1pt,auto,node distance=1.5cm,align=center,"
                                "thick,main node/.style={minimum size=25pt,fill=green!25,draw,"
                                "font=\\sffamily\\Large\\bfseries}]\n")
        except IOError:
            return None

    def write(self, ln):
        if not self.tikzfile is None:
            try:
                self.tikzfile.write(ln + "\n")
            except IOError:
                self.tikzfile = None
        
    def close(self):
        if not self.tikzfile.closed:
            self.write("    ;\n\\end{tikzpicture}\n\\end{figure}\n\end{document}\n")
            self.tikzfile.close()
            
            # Compile via pdflatex and convert to PNG
            try:
                basename = os.path.splitext(os.path.basename(self.texname))[0]
                FNULL = open(os.devnull, 'w')
                command = "pdflatex -halt-on-error " + self.texname + "; if convert -density 300 " + basename\
                          + ".pdf -trim -bordercolor White -border 10x10 +repage " + self.pngname + "; then\n  sleep 1\n"
                
                if self.cleanup:
                    command += "  rm " + basename + ".*\n"
                
                command += "fi"

                proc = subprocess.Popen(command, shell=True, cwd=self.outdir, stdout=FNULL)
                proc.wait()
            except OSError:
                pass
