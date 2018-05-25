# Author: David Smelt

import os
import subprocess

# Class for generating Tikz topology code,
# will be written to 'sim_output_directory/topo.tex'
# If imagemagick is installed, the topology is written to 'sim_output_directory/topology.png'

class TikzTopology():
    def __init__(self, outdir, nrows, ncols):
        # Use different base names for texname and pngname
        self.texname = "topo.tex"
        self.pngname = "topology.png"
        
        # rm `self.texname`.* after successful PNG generation
        self.cleanup = True 

        self.tikzfile = None
        self.outdir = outdir

        # Create output dir if it does not exist yet
        if not os.path.isdir(self.outdir):
            os.makedirs(self.outdir)

        node_dist = 1.5
        node_font = "\\Large"
        node_size = 25

        width = ncols * 0.8 if ncols == nrows else ncols * 1.2
        height = nrows * 0.8 if ncols == nrows else nrows * 1.2
        nrouters = ncols * nrows
        
        if ncols >= 32 or nrows >= 32 or nrouters >= 100:

            # Limit large scale topologies
            factor = nrouters / 100.0

            width *= factor
            height *= factor
            node_dist /= factor
            node_font = "\\small" if nrouters < 256 else "\\footnotesize"
            node_size /= factor

            width = min(40, width)
            height = min(40, height)
            node_dist = max(1, node_dist)
            node_size = max(10, node_size)

        try:
            self.tikzfile = open(os.path.join(self.outdir, self.texname), "w")
            self.tikzfile.write(
                "\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage{tikz}\n"
                "\\usepackage[letterpaper,paperwidth=" + str(width) + "in,paperheight="\
                + str(height) + "in]{geometry}\n\\geometry{margin=0.3in}\n\\usepackage{float}\n"
                "\\begin{document}\n\\pagenumbering{gobble}\n\\begin{figure}[p]\n\\centering\n"
                "\\begin{tikzpicture}[shorten >=1pt,auto,node distance=" + str(node_dist) +\
                "cm,align=center,thick,main node/.style={minimum size=" + str(int(node_size)) +\
                "pt,fill=green!25,draw,font=\\sffamily" + node_font + "\\bfseries}]\n")
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
