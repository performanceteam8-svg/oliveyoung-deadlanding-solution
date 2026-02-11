Attribute VB_Name = "DeadLandingUrlCheck"
Option Explicit

' ============================================================
' 데드랜딩 URL 점검 (중복 제거)
' - Link 시트에서 E열(영국)·F열(이스라엘) URL 수집 후 중복 제거
' - 각 URL 접속 검증 (정상/오류)
' - 기존 통합문서 안에 [URL] 시트를 만들고 결과 기록
' ============================================================

Private Const LINK_SHEET_NAME As String = "1) Link"  ' Link 탭 이름 (시트명이 다르면 여기 수정)
Private Const DATA_START_ROW As Long = 18            ' 데이터 시작 행 (17행이 헤더)
Private Const COL_E As Long = 5                       ' E열 영국
Private Const COL_F As Long = 6                       ' F열 이스라엘
Private Const HTTP_TIMEOUT_MS As Long = 8000          ' 요청 타임아웃 (밀리초)

Public Sub 데드랜딩_URL_점검_실행()
    Dim wb As Workbook
    Dim wsLink As Worksheet
    Dim wsURL As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim urlE As String
    Dim urlF As String
    Dim dictUK As Object
    Dim dictIL As Object
    Dim arrUK() As Variant
    Dim arrIL() As Variant
    Dim r As Long
    Dim cache As Object
    Dim result As String

    Set wb = ThisWorkbook
    On Error Resume Next
    Set wsLink = wb.Sheets(LINK_SHEET_NAME)
    On Error GoTo 0
    If wsLink Is Nothing Then
        MsgBox "시트 '" & LINK_SHEET_NAME & "'을(를) 찾을 수 없습니다. 시트명을 확인하세요.", vbExclamation
        Exit Sub
    End If

    lastRow = wsLink.Cells(wsLink.Rows.Count, COL_E).End(xlUp).Row
    If lastRow < DATA_START_ROW Then
        MsgBox "Link 시트에 데이터가 없습니다.", vbExclamation
        Exit Sub
    End If

    Set dictUK = CreateObject("Scripting.Dictionary")
    Set dictIL = CreateObject("Scripting.Dictionary")
    Set cache = CreateObject("Scripting.Dictionary")

    ' E열(영국)·F열(이스라엘) URL 수집 (중복 제거)
    For i = DATA_START_ROW To lastRow
        urlE = Trim(CStr(wsLink.Cells(i, COL_E).Value))
        urlF = Trim(CStr(wsLink.Cells(i, COL_F).Value))
        If IsValidUrl(urlE) And Not dictUK.Exists(urlE) Then dictUK.Add urlE, Empty
        If IsValidUrl(urlF) And Not dictIL.Exists(urlF) Then dictIL.Add urlF, Empty
    Next i

    ' [URL] 시트 생성 또는 비우기
    On Error Resume Next
    Set wsURL = wb.Sheets("[URL]")
    On Error GoTo 0
    If wsURL Is Nothing Then
        Set wsURL = wb.Sheets.Add(After:=wb.Sheets(wb.Sheets.Count))
        wsURL.Name = "[URL]"
    Else
        wsURL.Cells.Clear
    End If

    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    r = 1
    ' ---- 영국 ----
    wsURL.Cells(r, 1).Value = "영국"
    r = r + 1
    wsURL.Cells(r, 1).Value = "URL"
    wsURL.Cells(r, 2).Value = "검증결과"
    r = r + 1
    For Each urlE In dictUK.Keys
        result = CheckUrl(urlE, cache)
        wsURL.Cells(r, 1).Value = urlE
        wsURL.Cells(r, 2).Value = result
        r = r + 1
    Next urlE
    r = r + 1
    ' ---- 이스라엘 ----
    wsURL.Cells(r, 1).Value = "이스라엘"
    r = r + 1
    wsURL.Cells(r, 1).Value = "URL"
    wsURL.Cells(r, 2).Value = "검증결과"
    r = r + 1
    For Each urlF In dictIL.Keys
        result = CheckUrl(urlF, cache)
        wsURL.Cells(r, 1).Value = urlF
        wsURL.Cells(r, 2).Value = result
        r = r + 1
    Next urlF

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True

    wsURL.Activate
    MsgBox "URL 점검 완료. [URL] 시트를 확인하세요." & vbCrLf & _
           "영국: " & dictUK.Count & "개 (중복 제거)" & vbCrLf & _
           "이스라엘: " & dictIL.Count & "개 (중복 제거)", vbInformation
End Sub

Private Function IsValidUrl(ByVal s As String) As Boolean
    If Len(s) = 0 Then Exit Function
    If LCase(s) = "미운영" Then Exit Function
    If Left(s, 7) = "http://" Or Left(s, 8) = "https://" Then IsValidUrl = True
End Function

Private Function CheckUrl(ByVal url As String, ByRef cache As Object) As String
    Dim status As Long
    If cache.Exists(url) Then
        CheckUrl = cache(url)
        Exit Function
    End If
    status = GetHttpStatus(url)
    If status >= 200 And status < 400 Then
        CheckUrl = "정상"
    Else
        CheckUrl = "오류"
    End If
    cache.Add url, CheckUrl
End Function

Private Function GetHttpStatus(ByVal url As String) As Long
    On Error GoTo ErrHandler
    Dim http As Object
    Set http = CreateObject("WinHttp.WinHttpRequest.5.1")
    http.Open "GET", url, False
    http.setRequestHeader "User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    http.setTimeouts HTTP_TIMEOUT_MS, HTTP_TIMEOUT_MS, HTTP_TIMEOUT_MS, HTTP_TIMEOUT_MS
    http.Send
    GetHttpStatus = http.Status
    Exit Function
ErrHandler:
    GetHttpStatus = 0
End Function
