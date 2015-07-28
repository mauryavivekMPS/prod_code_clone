from __future__ import absolute_import

from celery import Task
import logging
from os import makedirs
import sendgrid
import datetime

from ivetl.common import common


class BaseTask(Task):
    abstract = True
    taskname = ''
    vizor = ''


    def getTaskLogger(self, path, taskname):

        ti_logger = logging.getLogger(path)

        fh = logging.FileHandler(path + "/" + taskname + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        ti_logger.addHandler(fh)

        return ti_logger

    def sendEmail(self, subject, body):

        try:
            sg = sendgrid.SendGridClient(common.SG_USERNAME, common.SG_PWD)

            message = sendgrid.Mail()
            message.add_to(common.EMAIL)
            message.set_subject(subject)
            message.set_html(body)
            message.set_from(common.FROM)

            sg.send(message)

        except Exception:
            # do nothing
            print("sending of email failed")


    def on_failure(self, exc, task_id, args, kwargs, einfo):

        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "ERROR! " + day + " - " + self.vizor + " - " + self.taskname

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.taskname

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Exception:</b> <br>"
        body += str(exc)

        body += "<br><br><b>Traceback:</b> <br>"
        body += einfo.traceback

        body += "<br><br><b>Command To Rerun Task:</b> <br>"
        body += self.__class__.__name__ + ".s" + str(args) + ".delay()"

        self.sendEmail(subject, body)

    def on_success(self, retval, task_id, args, kwargs):

        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + self.vizor + " - " + self.taskname

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.taskname

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)

        self.sendEmail(subject, body)




