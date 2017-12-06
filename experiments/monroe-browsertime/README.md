# Browsertime - Your browser, your page, your scripts!


Access the Web Performance Timeline, from your browser, in your terminal!

Browsertime allows you to:
 1. Query timing data directly from the browser, to access [Navigation Timing](http://kaaes.github.io/timing/info.html), [User Timing](http://www.html5rocks.com/en/tutorials/webperformance/usertiming/),
[Resource Timing](http://www.w3.org/TR/resource-timing/), first paint and [RUM Speed Index](https://github.com/WPO-Foundation/RUM-SpeedIndex).
 1. Generate [HAR](http://www.softwareishard.com/blog/har-12-spec/) files (using [HAR Export trigger](https://github.com/firebug/har-export-trigger) for Firefox and parsing the Chrome log for Chrome).
 1. Run custom Javascript scripts in the browser and get statistics for each run.
 1. Record a video of the screen and analyze the result to get First Visual Change, Speed Index, Visual Complete 85 % and Last Visual Change.

## A simple example

<pre>
$ bin/browsertime.js https://www.sitespeed.io
</pre>

Load https://www.sitespeed.io/ in Chrome three times. Results are stored in a JSON file (browsertime.json) with the timing data, and a HAR file (browsertime.har) in browsertime-results/www.sitespeed.io/$date/


## Browsers
Browsertime supports Firefox and Chrome on desktop. On Android we support Chrome.

But we want to [support Opera (on Android)](https://github.com/tobli/browsertime/issues/150)  and when(?!) iOS Safari supports WebDriver we will add that too.

## How does it work
Browsertime uses Selenium NodeJS to drive the browser. It starts the browser, load a URL, executes configurable Javascripts to collect metrics, collect a HAR file.

To get the HAR from Firefox we use the [HAR Export Trigger](https://github.com/firebug/har-export-trigger) and Chrome we use [Chrome-HAR](https://github.com/sitespeedio/chrome-har) to parse the timeline log and generate the HAR file.

Oh and you can run your own Selenium script before (<code>--preScript</code>) and after (<code>--postScript</code>) a URL is accessed so you can login/logout or do whatever you want.

