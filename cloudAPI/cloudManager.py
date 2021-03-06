from loginSystem.models import Administrator
from django.shortcuts import HttpResponse
import json
from plogical.website import WebsiteManager
from plogical.acl import ACLManager
from plogical.virtualHostUtilities import virtualHostUtilities
from websiteFunctions.models import Websites
import subprocess, shlex
from databases.databaseManager import DatabaseManager
from dns.dnsManager import DNSManager
from mailServer.mailserverManager import MailServerManager
from ftp.ftpManager import FTPManager
from manageSSL.views import issueSSL, obtainHostNameSSL, obtainMailServerSSL
from plogical.backupManager import BackupManager
import userManagment.views as um
from packages.packagesManager import PackagesManager
from plogical.processUtilities import ProcessUtilities
from firewall.firewallManager import FirewallManager
from serverLogs.views import getLogsFromFile

class CloudManager:
    def __init__(self, data=None, admin = None):
        self.data = data
        self.admin = admin

    def ajaxPre(self, status, errorMessage):
        final_dic = {'status': status, 'error_message': errorMessage}
        final_json = json.dumps(final_dic)
        return HttpResponse(final_json)

    def verifyLogin(self, request):
        try:
            if request.META['HTTP_AUTHORIZATION'] == self.admin.token:
                return 1, self.ajaxPre(1, None)
            else:
                return 0, self.ajaxPre(0, 'Invalid login information.')

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchWebsites(self):
        try:
            wm = WebsiteManager()
            return wm.getFurtherAccounts(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitWebsiteDeletion(self, request):
        try:
            request.session['userID'] = self.admin.pk
            wm = WebsiteManager()
            return wm.submitWebsiteDeletion(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitWebsiteCreation(self):
        try:
            wm = WebsiteManager()
            return wm.submitWebsiteCreation(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchWebsiteDataJSON(self):
        try:
            wm = WebsiteManager()
            return wm.fetchWebsiteDataJSON(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchWebsiteData(self):
        try:
            currentACL = ACLManager.loadedACL(self.admin.pk)
            website = Websites.objects.get(domain=self.data['domainName'])
            admin = Administrator.objects.get(pk=self.admin.pk)

            if ACLManager.checkOwnership(self.data['domainName'], admin, currentACL) == 1:
                pass
            else:
                return ACLManager.loadErrorJson()

            Data = {}

            Data['ftpAllowed'] = website.package.ftpAccounts
            Data['ftpUsed'] = website.users_set.all().count()

            Data['dbUsed'] = website.databases_set.all().count()
            Data['dbAllowed'] = website.package.dataBases

            diskUsageDetails = virtualHostUtilities.getDiskUsage("/home/" + self.data['domainName'],
                                                                 website.package.diskSpace)

            ## bw usage calculation

            try:
                execPath = "sudo python " + virtualHostUtilities.cyberPanel + "/plogical/virtualHostUtilities.py"
                execPath = execPath + " findDomainBW --virtualHostName " + self.data[
                    'domainName'] + " --bandwidth " + str(
                    website.package.bandwidth)

                output = subprocess.check_output(shlex.split(execPath))
                bwData = output.split(",")
            except BaseException:
                bwData = [0, 0]

            ## bw usage calculations

            Data['bwAllowed'] = website.package.bandwidth
            Data['bwUsed'] = bwData[0]
            Data['bwUsage'] = bwData[1]

            if diskUsageDetails != None:
                if diskUsageDetails[1] > 100:
                    diskUsageDetails[1] = 100

                Data['diskUsage'] = diskUsageDetails[1]
                Data['diskUsed'] = diskUsageDetails[0]
                Data['diskAllowed'] = website.package.diskSpace
            else:
                Data['diskUsed'] = 0
                Data['diskUsage'] = 0
                Data['diskInMBTotal'] = website.package.diskSpace

            Data['status'] = 1
            final_json = json.dumps(Data)
            return HttpResponse(final_json)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchModifyData(self):
        try:
            wm = WebsiteManager()
            return wm.submitWebsiteModify(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def saveModifications(self):
        try:
            wm = WebsiteManager()
            return wm.saveWebsiteChanges(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitDBCreation(self):
        try:
            dm = DatabaseManager()
            return dm.submitDBCreation(self.admin.pk, self.data, 1)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchDatabases(self):
        try:
            dm = DatabaseManager()
            return dm.fetchDatabases(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitDatabaseDeletion(self):
        try:
            dm = DatabaseManager()
            return dm.submitDatabaseDeletion(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changePassword(self):
        try:
            dm = DatabaseManager()
            return dm.changePassword(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getCurrentRecordsForDomain(self):
        try:
            dm = DNSManager()
            return dm.getCurrentRecordsForDomain(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteDNSRecord(self):
        try:
            dm = DNSManager()
            return dm.deleteDNSRecord(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def addDNSRecord(self):
        try:
            dm = DNSManager()
            return dm.addDNSRecord(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitEmailCreation(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.submitEmailCreation()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getEmailsForDomain(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.getEmailsForDomain()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitEmailDeletion(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.submitEmailDeletion()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitPasswordChange(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.submitPasswordChange()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchCurrentForwardings(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.fetchCurrentForwardings()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitForwardDeletion(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.submitForwardDeletion()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitEmailForwardingCreation(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.submitEmailForwardingCreation()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchDKIMKeys(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.fetchDKIMKeys()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def generateDKIMKeys(self, request):
        try:
            request.session['userID'] = self.admin.pk
            msm = MailServerManager(request)
            return msm.generateDKIMKeys()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitFTPCreation(self, request):
        try:
            request.session['userID'] = self.admin.pk
            fm = FTPManager(request)
            return fm.submitFTPCreation()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getAllFTPAccounts(self, request):
        try:
            request.session['userID'] = self.admin.pk
            fm = FTPManager(request)
            return fm.getAllFTPAccounts()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitFTPDelete(self, request):
        try:
            request.session['userID'] = self.admin.pk
            fm = FTPManager(request)
            return fm.submitFTPDelete()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changeFTPPassword(self, request):
        try:
            request.session['userID'] = self.admin.pk
            fm = FTPManager(request)
            return fm.changePassword()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def issueSSL(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return issueSSL(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def statusFunc(self):
        try:
            statusFile = self.data['statusFile']
            statusData = open(statusFile, 'r').readlines()
            lastLine = statusData[-1]

            if lastLine.find('[200]') > -1:
                command = 'sudo rm -f ' + statusFile
                subprocess.call(shlex.split(command))
                data_ret = {'status': 1, 'abort': 1, 'installationProgress': "100", 'currentStatus': lastLine}
                json_data = json.dumps(data_ret)
                return HttpResponse(json_data)
            elif lastLine.find('[404]') > -1:
                data_ret = {'status': 0, 'abort': 1, 'installationProgress': "0", 'error_message': lastLine}
                json_data = json.dumps(data_ret)
                return HttpResponse(json_data)
            else:
                progress = lastLine.split(',')
                currentStatus = progress[0]
                try:
                    installationProgress = progress[1]
                except:
                    installationProgress = 0
                data_ret = {'status': 1, 'abort': 0, 'installationProgress': installationProgress,
                            'currentStatus': currentStatus}
                json_data = json.dumps(data_ret)
                return HttpResponse(json_data)

        except BaseException, msg:
            data_ret = {'status': 0, 'abort': 0, 'installationProgress': "0", 'errorMessage': str(msg)}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)

    def submitDomainCreation(self):
        try:
            wm = WebsiteManager()
            return wm.submitDomainCreation(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchDomains(self):
        try:
            wm = WebsiteManager()
            return wm.fetchDomains(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitDomainDeletion(self):
        try:
            wm = WebsiteManager()
            return wm.submitDomainDeletion(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changeOpenBasedir(self):
        try:
            wm = WebsiteManager()
            return wm.changeOpenBasedir(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changePHP(self):
        try:
            wm = WebsiteManager()
            return wm.changePHP(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def backupStatusFunc(self):
        try:
            bm = BackupManager()
            return bm.backupStatus(self.admin.pk, self.data)

        except BaseException, msg:
            data_ret = {'status': 0, 'abort': 0, 'installationProgress': "0", 'errorMessage': str(msg)}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)

    def submitBackupCreation(self):
        try:
            bm = BackupManager()
            return bm.submitBackupCreation(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getCurrentBackups(self):
        try:
            bm = BackupManager()
            return bm.getCurrentBackups(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteBackup(self):
        try:
            bm = BackupManager()
            return bm.deleteBackup(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchACLs(self):
        try:
            userID = self.admin.pk
            currentACL = ACLManager.loadedACL(userID)

            if currentACL['admin'] == 1:
                aclNames = ACLManager.unFileteredACLs()
            elif currentACL['changeUserACL'] == 1:
                aclNames = ACLManager.unFileteredACLs()
            elif currentACL['createNewUser'] == 1:
                aclNames = ['user']
            else:
                return ACLManager.loadError()

            json_data = "["
            checker = 0

            for items in aclNames:
                dic = {'acl': items}

                if checker == 0:
                    json_data = json_data + json.dumps(dic)
                    checker = 1
                else:
                    json_data = json_data + ',' + json.dumps(dic)

            json_data = json_data + ']'
            final_json = json.dumps({'status': 1, 'error_message': "None", "data": json_data})
            return HttpResponse(final_json)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitUserCreation(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.submitUserCreation(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchUsers(self):
        try:
            userID = self.admin.pk
            allUsers = ACLManager.loadUserObjects(userID)

            json_data = "["
            checker = 0

            for user in allUsers:
                dic = {
                    "id": user.id,
                    "userName": user.userName,
                    "firstName": user.firstName,
                    "lastName": user.lastName,
                    "email": user.email,
                    "acl": user.acl.name,
                    "websitesLimit": user.initWebsitesLimit
                }

                if checker == 0:
                    json_data = json_data + json.dumps(dic)
                    checker = 1
                else:
                    json_data = json_data + ',' + json.dumps(dic)

            json_data = json_data + ']'
            final_json = json.dumps({'status': 1, 'error_message': "None", "data": json_data})
            return HttpResponse(final_json)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitUserDeletion(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.submitUserDeletion(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def saveModificationsUser(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.saveModifications(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def userWithResellerPriv(self):
        try:
            userID = self.admin.pk
            allUsers = ACLManager.userWithResellerPriv(userID)

            json_data = "["
            checker = 0

            for user in allUsers:
                dic = {
                    "userName": user,
                }

                if checker == 0:
                    json_data = json_data + json.dumps(dic)
                    checker = 1
                else:
                    json_data = json_data + ',' + json.dumps(dic)

            json_data = json_data + ']'
            final_json = json.dumps({'status': 1, 'error_message': "None", "data": json_data})
            return HttpResponse(final_json)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def saveResellerChanges(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.saveResellerChanges(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changeACLFunc(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.changeACLFunc(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def createACLFunc(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.createACLFunc(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def findAllACLs(self, request):
        try:
            userID = self.admin.pk
            currentACL = ACLManager.loadedACL(userID)

            if currentACL['admin'] == 1:
                aclNames = ACLManager.findAllACLs()
            else:
                return ACLManager.loadErrorJson()

            json_data = "["
            checker = 0

            for items in aclNames:
                dic = {'acl': items}

                if checker == 0:
                    json_data = json_data + json.dumps(dic)
                    checker = 1
                else:
                    json_data = json_data + ',' + json.dumps(dic)

            json_data = json_data + ']'
            final_json = json.dumps({'status': 1, 'error_message': "None", "data": json_data})
            return HttpResponse(final_json)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteACLFunc(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.deleteACLFunc(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchACLDetails(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.fetchACLDetails(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitACLModifications(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return um.submitACLModifications(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitPackage(self, request):
        try:
            request.session['userID'] = self.admin.pk
            pm = PackagesManager(request)
            return pm.submitPackage()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchPackages(self, request):
        try:
            userID = self.admin.pk
            currentACL = ACLManager.loadedACL(userID)

            if ACLManager.currentContextPermission(currentACL, 'deletePackage') == 0:
                return ACLManager.loadError()

            packageList = ACLManager.loadPackageObjects(userID, currentACL)

            json_data = "["
            checker = 0

            for items in packageList:
                dic = {
                    'packageName': items.packageName,
                    'allowedDomains': items.allowedDomains,
                    'diskSpace': items.diskSpace,
                    'bandwidth': items.bandwidth,
                    'emailAccounts': items.emailAccounts,
                    'dataBases': items.dataBases,
                    'ftpAccounts': items.ftpAccounts,
                }

                if checker == 0:
                    json_data = json_data + json.dumps(dic)
                    checker = 1
                else:
                    json_data = json_data + ',' + json.dumps(dic)

            json_data = json_data + ']'
            final_json = json.dumps({'status': 1, 'error_message': "None", "data": json_data})
            return HttpResponse(final_json)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitPackageDelete(self, request):
        try:
            pm = PackagesManager(request)
            return pm.submitDelete()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitPackageModify(self, request):
        try:
            pm = PackagesManager(request)
            return pm.saveChanges()
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getDataFromLogFile(self, request):
        try:
            wm = WebsiteManager()
            return wm.getDataFromLogFile(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def fetchErrorLogs(self, request):
        try:
            wm = WebsiteManager()
            return wm.fetchErrorLogs(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def submitApplicationInstall(self, request):
        try:
            request.session['userID'] = self.admin.pk
            wm = WebsiteManager()

            if self.data['selectedApplication'] == 'WordPress with LSCache':
                return wm.installWordpress(self.admin.pk, self.data)
            elif self.data['selectedApplication'] == 'Prestashop':
                return wm.prestaShopInstall(self.admin.pk, self.data)
            elif self.data['selectedApplication'] == 'Joomla':
                return wm.installJoomla(self.admin.pk, self.data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def obtainServer(self, request):
        try:
            request.session['userID'] = self.admin.pk
            data_ret = {'status': 1, 'serverStatus': ProcessUtilities.decideServer()}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getSSHConfigs(self):
        try:
            fm = FirewallManager()
            return fm.getSSHConfigs(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def saveSSHConfigs(self):
        try:
            fm = FirewallManager()
            return fm.saveSSHConfigs(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteSSHKey(self):
        try:
            fm = FirewallManager()
            return fm.deleteSSHKey(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def addSSHKey(self):
        try:
            fm = FirewallManager()
            return fm.addSSHKey(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getCurrentRules(self):
        try:
            fm = FirewallManager()
            return fm.getCurrentRules(self.admin.pk)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def addRule(self):
        try:
            fm = FirewallManager()
            return fm.addRule(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteRule(self):
        try:
            fm = FirewallManager()
            return fm.deleteRule(self.admin.pk, self.data)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def getLogsFromFile(self, request):
        try:
            request.session['userID'] = self.admin.pk
            return getLogsFromFile(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def serverSSL(self, request):
        try:
            request.session['userID'] = self.admin.pk
            if self.data['type'] == 'hostname':
                return obtainHostNameSSL(request)
            else:
                return obtainMailServerSSL(request)
        except BaseException, msg:
            return self.ajaxPre(0, str(msg))
