import cx_Oracle

files = [
"CNI_PERSONAL_01.dat",
"CNI_PERSONAL_02.dat",
"CNI_PERSONAL_03.dat",
"CNI_PERSONAL_04.dat",
"CNI_PERSONAL_05.dat",
"CNI_PERSONAL_06.dat",
"CNI_PERSONAL_07.dat",
"CNI_PERSONAL_08.dat",
"CNI_PERSONAL_09.dat",
"CNI_PERSONAL_10.dat",
"CNI_PERSONAL_11.dat",
"CNI_PERSONAL_12.dat",
"CNI_PERSONAL_13.dat",
"CNI_PERSONAL_14.dat",
"CNI_PERSONAL_15.dat",
"CNI_PERSONAL_16.dat",
"CNI_PERSONAL_17.dat",
"CNI_PERSONAL_18.dat",
"CNI_PERSONAL_19.dat",
"CNI_PERSONAL_20.dat",
"CNI_PERSONAL_21.dat",
"CNI_PERSONAL_22.dat",
"CNI_PERSONAL_23.dat",
"CNI_PERSONAL_24.dat",
"CNI_PERSONAL_25.dat",
"CNI_PERSONAL_26.dat",
"CNI_PERSONAL_27.dat",
"CNI_PERSONAL_28.dat",
"CNI_PERSONAL_29.dat",
"CNI_PERSONAL_30.dat",
"CNI_PERSONAL_31.dat",
"CNI_PERSONAL_32.dat"

]

# files = ["CNI_Persona_01A05.DAT"]

conf = {
    'batchSize': 100,
    'tableName': "",
    'rowLimit': -1,
    'oracleConn': {
        'hostName': "localhost",
        'portNumber': "1521",
        'serviceName': "BBDDOracXDB",
        'userName': "CSNISPRNPSP",
        'pwd': "S1scool"
    },
    'fileName': "" ,
    'fileDef': "estructura.txt",
    'tableDef': {
        'schema': "CSNISPRNPSP",
        'tableName': "Z_PYLOAD_RNPSP_FEB2026",
        'truncate': True
    }
}

#fileFullPath = "E:\\RESPALDO_PCs_BBDD\\JUAN\\FTP\\octubre 2020\\{fileName}"
fileFullPath = "/home/carpeta-bbdd/202310/persona202310/{fileName}"
#//.format(fileName=conf['fileName'])
batchData = []

rowRead = 0

# print (fileFullPath)





######################################################################################################################
def createConnection(oracleConn):
    dsn_tns = cx_Oracle.makedsn(oracleConn['hostName'], oracleConn['portNumber'], service_name=oracleConn['serviceName'])
    conn = cx_Oracle.connect(user=oracleConn['userName'], password=oracleConn['pwd'], dsn=dsn_tns)
    return conn


######################################################################################################################
def executeBatch(batchData, conn, tableDefLen):
    # print("executing batch ini {strRowRead}".format(strRowRead=rowRead))
    
    insertPlacheHolder = ""
    for i in range(tableDefLen):
        insertPlacheHolder += ":{num}, ".format(num=i+1)
    insertPlacheHolder += ":{num} ".format(num=tableDefLen)
    
    cur = conn.cursor()
    sql = """insert into {tableName} values({insPlaceHolder})""".format(tableName=conf['tableName'], insPlaceHolder=insertPlacheHolder)
    # print(sql)
    cur.executemany(sql, batchData)
    conn.commit()
    cur.close()
    batchData.clear()
    # print("executing batch end {strRowRead}".format(strRowRead=rowRead))
    return



######################################################################################################################
def processRow(row, conn, tableDefList):
    batchData.append(tuple(row))
    strRowRead = str(rowRead)

    # print(len(batchData))
    if len(batchData) > conf['batchSize']:
        
        executeBatch(batchData, conn, len(tableDefList))
        
    return



######################################################################################################################
###### LECTURA DE FILAS
def parseRnpspLine(line, tableDefList):
    list = []
    
    pos1 = 0
    pos2 = 0
    
    i = 0
    for item in tableDefList:
        pos1 = item[1] - 1
        pos2 = pos1 + fileDef_getColLen(tableDefList, i)
        list.append(line[pos1:pos2].strip())
        i += 1
    list.append(conf['fileName'])
    
    #print(list)
    
    return list



######################################################################################################################
#### CODIFICACION DEL ARCHIVO
def processSingleFile(filename, tableDefList):
    global rowRead
    global conf
    
    conf['tableName'] = '{SCHEMA}.{TABLE}'.format(SCHEMA=conf['tableDef']['schema'], TABLE=conf['tableDef']['tableName'])
    conf['fileName'] = filename
    conn = createConnection(conf['oracleConn'])
    #with open(fileFullPath.format(fileName=filename), encoding="utf-8-sig") as f:
    with open(fileFullPath.format(fileName=filename), encoding="latin-1") as f:
        for line in f:
            #rowRead = rowRead + 1
            #print(parseRnpspLine(line, tableDefList))
            processRow(parseRnpspLine(line, tableDefList), conn, tableDefList)
            rowRead = rowRead + 1
            if rowRead > (conf['rowLimit']-1) and conf['rowLimit'] != -1:
               print("breking loop")
               break
    print(rowRead)
    # print(len(batchData))
    if len(batchData) > 0:
        print("execute last insert")
        executeBatch(batchData, conn, len(tableDefList))

    conn.close()
        # print(parseRnpspLine(f.readline()))
        # print(f"sadfsadfasdf {conf['tableName']} sdafsdsadf")
        # print()
    return


def loopFiles(tableDefList):
    fullFileName = ""
    global rowRead
    for file in files:
        rowRead = 0
        print("Processsing file: {fileName}".format(fileName=file))
        processSingleFile(file, tableDefList)
        print("End Processsing file: {fileName}".format(fileName=file))
        #fullFileName = fileFullPath.format(fileName=file)
        #print(fullFileName)
    return
        
        
def fileDef_getColLen(tableColDefList, pos):
    colLen = -1
    
    if pos > len(tableColDefList)-1:
        return colLen
    
    if pos == len(tableColDefList)-1:
        colLen = tableColDefList[pos][2] - tableColDefList[pos][1]
    else:
        colLen = tableColDefList[pos+1][1] - tableColDefList[pos][1]
    
    return colLen   



def genCreateTable(tableColDef):
    global conf
    curPos = 0
    colTemplate = "{colName} {dataType} ({len}),"
    colsStr = ""
    for item in tableColDef:
        colsStr+= colTemplate.format(colName=item[0], dataType="VARCHAR", len=fileDef_getColLen(tableColDef, curPos))
        curPos += 1
        
    # anadir columna de nombre del archivo
    colsStr += "TEXTFILENAME VARCHAR(200)  "
    temp = "CREATE TABLE {schema}.{tableName} ( {cols} )".format(schema=conf['tableDef']['schema'], tableName=conf['tableDef']['tableName'], cols=colsStr[:-1])
    # CUANDO EXCEDE HAY MAS DE 4000 PARA UN VARCHAR
    temp= temp.replace('4001','4000')
    #print(temp)
    return temp
    
    
def readFileDef():
    tableColDef = []
    
    with open(fileFullPath.format(fileName=conf['fileDef']), encoding="latin-1") as f:
    #with open(fileFullPath.format(fileName=conf['fileDef']), encoding="utf-8-sig") as f:
    
        for line in f:
            colList = line.split(" ")
            #print (colList[0])
            #print (colList[2].split(":")[0].replace("(", ""))
            #print (colList[2].split(":")[1].replace(")", ""))
            tableColDef.append( (colList[0], int(colList[2].split(":")[0].replace("(", "")), int(colList[2].split(":")[1].replace(")", ""))))
    
    #print(tableColDef)
    #print(fileDef_getColLen(tableColDef,2))
    #print(fileDef_getColLen(tableColDef,28))
    
    #genCreateTable(tableColDef)
    return tableColDef
    
def attemptCreateTable(sqlCreate, conn):
    sqlTemplate = """
        declare
        v_sql LONG;
        begin

        v_sql:='{createTable}';
        execute immediate v_sql;

        EXCEPTION
            WHEN OTHERS THEN
              IF SQLCODE = -955 THEN
                NULL; -- suppresses ORA-00955 exception
              ELSE
                 RAISE;
              END IF;
        END; 
    """.format(createTable=sqlCreate)
    
    
    
    # Ejecutar 
    print(sqlTemplate)
    cur = conn.cursor()
    cur.execute(sqlTemplate) 
    cur.close()
    
    
    if conf['tableDef']['truncate'] == True :
        cur = conn.cursor()
        cur.execute(' TRUNCATE TABLE {SCHEMA}.{TABLE}'.format(SCHEMA=conf['tableDef']['schema'], TABLE=conf['tableDef']['tableName'])) 
        cur.close()
        


        
    
    
tableDefList = readFileDef()
# print(len(tableDefList))
sqlCreate = genCreateTable(tableDefList)
# print(sqlCreate)
conn = createConnection(conf['oracleConn'])
attemptCreateTable(sqlCreate, conn)
conn.close()
loopFiles(tableDefList)
        















