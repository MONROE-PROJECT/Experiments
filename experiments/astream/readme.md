
AStream container for MONROE

AStream is a Python based emulated video player to evalutae the perfomance of the DASH bitrate adaptation algorithms. 
The rate adaptation algorithms supported are the following:
* basic adaptation
* Segment Aware Rate Adaptation (SARA): P. Juluri, V. Tamarapalli, and D. Medhi, “SARA: Segment Aware Rate Adaptation algorithm for Dynamic Adaptive Streaming over HTTP,” in ICC QoE-FI Workshop, June, 2015
* Buffer-Based Rate Adaptation (Netflix): This is based on the algorithm presented in the paper: Te-Yuan Huang, Ramesh Johari, Nick McKeown, Matthew Trunnell, and Mark Watson. 2014. A buffer-based approach to rate adaptation: evidence from a large video streaming service. In Proceedings of the 2014 ACM conference on SIGCOMM (SIGCOMM '14). ACM, New York, NY, USA, 187-198. DOI=10.1145/2619239.2626296 http://doi.acm.org/10.1145/2619239.262629

The experimenter can choose the rate adaptation algorithm by passing a JSON string to the scheduler through the user interface (e.g., "playback":"NETFLIX"). The default is the basic adaptation scheme. 
Also, the user can specify the target MPD file to play (e.g., "mpd_file":"http://128.39.37.161:8080/BigBuckBunny_4s.mpd") and the number of segments to retrieve (e.g., "segment_limit":10).

The astream container outputs two log files:
1) Buffer logs: epoch time, current playback time, current buffer size (in segments), current playback state.
2) Playback logs: epoch time, playback time, segment number, segment size, playback bitrate, segment duration, weighted harmonic mean average download rate 

