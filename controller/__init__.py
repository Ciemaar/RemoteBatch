import sip

sip.setapi('QVariant', 2)

from view import AddJobDialog, ManagerMain


def mgr_main(queue):
    main = ManagerMain(queue)
    main.refresh()
    main.show()
    return main


def job_dialog(path, queue):
    tabdialog = AddJobDialog(queue)
    print "created tabdialog"
    return tabdialog.exec_()
