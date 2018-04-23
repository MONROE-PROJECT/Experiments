
MONROE-AStream Client Container

AStream is a Python based emulated video player to evaluate the perfomance of DASH bitrate adaptation algorithms. 

The rate adaptation algorithms supported are the following:
* basic adaptation
* Segment Aware Rate Adaptation (SARA): P. Juluri, V. Tamarapalli, and D. Medhi, “SARA: Segment Aware Rate Adaptation algorithm for Dynamic Adaptive Streaming over HTTP,” in ICC QoE-FI Workshop, June, 2015
* Buffer-Based Rate Adaptation (Netflix): This is based on the algorithm presented in the paper: Te-Yuan Huang, Ramesh Johari, Nick McKeown, Matthew Trunnell, and Mark Watson. 2014. A buffer-based approach to rate adaptation: evidence from a large video streaming service. In Proceedings of the 2014 ACM conference on SIGCOMM (SIGCOMM '14). ACM, New York, NY, USA, 187-198. DOI=10.1145/2619239.2626296 http://doi.acm.org/10.1145/2619239.262629

Experimenters can choose the rate adaptation algorithm by passing a JSON string to the scheduler through the user interface (e.g., "cnf_astream_playback":"SARA"). The default is basic adaptation.

Experimenters can also specify the target MPD file (e.g., "cnf_astream_mpd":"http://www-itec.uni-klu.ac.at/ftp/datasets/mmsys12/BigBuckBunny/bunny_2s/BigBuckBunny_2s_isoffmain_DIS_23009_1_v_2_1c2_2011_08_30.mpd") and the number of segments to retrieve (e.g., "cnf_astream_segment_limit":10).

The MONROE-AStream container outputs two files:
1) Summary JSON describing the experiment.
2) Compressed archive containing runtime log, segment log, buffer log, and downloaded video segments.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
