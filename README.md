# TA-debug-interface

This is a very simple flask-based web app which was developed to serve as an interface for a study about TAs debugging student code.

In its current form, it is inteded to be run *only* on a local computer controlled by the researcher during a live study session, not deployed on the web. In particular, note that:

- User code is executed directly, without any safety or security checks
- There is litte functionality for navigating between problems, aside from automatically advancing to the next one; The server is intended to be restarted for each new study, and shut down after the study.

In order to run a study remotely (e.g. while communicating with the participant over Zoom), you can run the server locally and then create a tunnel with something like [ngrok](https://ngrok.com/)

