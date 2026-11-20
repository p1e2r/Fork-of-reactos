/*
 * PROJECT:     ReactOS Explorer (Lumen fork)
 * LICENSE:     LGPL-2.1-or-later (https://spdx.org/licenses/LGPL-2.1-or-later)
 * PURPOSE:     Windows 11-style start menu: centered panel with a search box,
 *              a grid of pinned apps, recent files, "All apps" and a power button.
 */

#include "precomp.h"
#include <windowsx.h>

#define LS_CLASSNAME        L"LumenStartMenu"
#define LS_WIDTH            600
#define LS_MAXHEIGHT        640
#define LS_MARGIN           24
#define LS_GAP              12
#define LS_COLS             6
#define LS_CELL_H           84
#define LS_REC_ROW_H        52
#define LS_LIST_ROW_H       36
#define LS_BOTTOM_H         64
#define LS_MAX_APPS         512
#define LS_MAX_PINS         12
#define LS_MAX_RECENT       6
#define LS_MAX_HITS         (LS_MAX_APPS + 64)
#define IDC_LS_SEARCH       100

/* Colors */
#define CLR_BG              RGB(243, 243, 243)
#define CLR_BORDER          RGB(208, 208, 208)
#define CLR_BOTTOM          RGB(235, 235, 235)
#define CLR_HOVER           RGB(228, 228, 228)
#define CLR_TEXT            RGB(26, 26, 26)
#define CLR_TEXT_DIM        RGB(110, 110, 110)
#define CLR_ACCENT          RGB(0, 95, 184)
#define CLR_SEARCH_BG       RGB(255, 255, 255)
#define CLR_SEARCH_BORDER   RGB(220, 220, 220)

enum LS_VIEW { LSV_HOME, LSV_ALLAPPS, LSV_SEARCH };
enum LS_HIT { LSH_NONE, LSH_PIN, LSH_RECENT, LSH_APP, LSH_ALLAPPS, LSH_BACK, LSH_POWER, LSH_USER };

struct LS_ITEM
{
    WCHAR szName[MAX_PATH];
    WCHAR szPath[MAX_PATH];
    WCHAR szArgs[MAX_PATH];
    HICON hIcon;      /* 32x32 */
    HICON hIconSmall; /* 16x16 */
};

struct LS_HITRECT
{
    RECT rc;
    LS_HIT kind;
    INT index;
};

static HWND g_hwndMenu = NULL;
static HWND g_hwndSearch = NULL;
static HWND g_hwndTray = NULL;
static WNDPROC g_pfnEditProc = NULL;
static HFONT g_hFont = NULL, g_hFontBold = NULL, g_hFontSmall = NULL;
static LS_VIEW g_View = LSV_HOME;
static LS_ITEM g_Pins[LS_MAX_PINS];
static INT g_cPins = 0;
static LS_ITEM g_Recent[LS_MAX_RECENT];
static INT g_cRecent = 0;
static LS_ITEM *g_Apps = NULL;
static INT g_cApps = 0;
static INT g_Filtered[LS_MAX_APPS];
static INT g_cFiltered = 0;
static LS_HITRECT g_Hits[LS_MAX_HITS];
static INT g_cHits = 0;
static INT g_iHot = -1;
static INT g_Scroll = 0;
static INT g_Height = LS_MAXHEIGHT;
static DWORD g_dwHiddenTick = 0;
static RECT g_rcStartButton;
static WCHAR g_szUser[64];

/* ------------------------------------------------------------------ items */

static VOID LS_FreeItem(LS_ITEM *pItem)
{
    if (pItem->hIcon)
        DestroyIcon(pItem->hIcon);
    if (pItem->hIconSmall)
        DestroyIcon(pItem->hIconSmall);
    pItem->hIcon = pItem->hIconSmall = NULL;
}

static VOID LS_LoadIcons(LS_ITEM *pItem, LPCITEMIDLIST pidl)
{
    SHFILEINFOW sfi;
    UINT uFlags = pidl ? SHGFI_PIDL : 0;
    LPCWSTR pszSource = pidl ? (LPCWSTR)pidl : pItem->szPath;

    ZeroMemory(&sfi, sizeof(sfi));
    if (SHGetFileInfoW(pszSource, 0, &sfi, sizeof(sfi), uFlags | SHGFI_ICON | SHGFI_LARGEICON))
        pItem->hIcon = sfi.hIcon;
    ZeroMemory(&sfi, sizeof(sfi));
    if (SHGetFileInfoW(pszSource, 0, &sfi, sizeof(sfi), uFlags | SHGFI_ICON | SHGFI_SMALLICON))
        pItem->hIconSmall = sfi.hIcon;
}

static VOID LS_AddPin(LPCWSTR pszName, LPCWSTR pszExe, LPCWSTR pszArgs, INT csidlIcon)
{
    LS_ITEM *pItem;
    WCHAR szPath[MAX_PATH];

    if (g_cPins >= LS_MAX_PINS)
        return;
    if (!SearchPathW(NULL, pszExe, NULL, _countof(szPath), szPath, NULL))
        return;

    pItem = &g_Pins[g_cPins++];
    ZeroMemory(pItem, sizeof(*pItem));
    StringCchCopyW(pItem->szName, _countof(pItem->szName), pszName);
    StringCchCopyW(pItem->szPath, _countof(pItem->szPath), szPath);
    StringCchCopyW(pItem->szArgs, _countof(pItem->szArgs), pszArgs);

    if (csidlIcon >= 0)
    {
        LPITEMIDLIST pidl = NULL;
        if (SUCCEEDED(SHGetSpecialFolderLocation(NULL, csidlIcon, &pidl)))
        {
            LS_LoadIcons(pItem, pidl);
            CoTaskMemFree(pidl);
        }
    }
    if (!pItem->hIcon)
        LS_LoadIcons(pItem, NULL);
}

static VOID LS_LoadPins(VOID)
{
    if (g_cPins)
        return;

    LS_AddPin(L"File Explorer", L"explorer.exe", L"", CSIDL_DRIVES);
    LS_AddPin(L"Settings", L"control.exe", L"", CSIDL_CONTROLS);
    LS_AddPin(L"Apps", L"rapps.exe", L"", -1);
    LS_AddPin(L"Command Prompt", L"cmd.exe", L"", -1);
    LS_AddPin(L"Notepad", L"notepad.exe", L"", -1);
    LS_AddPin(L"Paint", L"mspaint.exe", L"", -1);
    LS_AddPin(L"Calculator", L"calc.exe", L"", -1);
    LS_AddPin(L"WordPad", L"wordpad.exe", L"", -1);
    LS_AddPin(L"Task Manager", L"taskmgr.exe", L"", -1);
    LS_AddPin(L"Media Player", L"mplay32.exe", L"", -1);
    LS_AddPin(L"Character Map", L"charmap.exe", L"", -1);
    LS_AddPin(L"Recycle Bin", L"explorer.exe", L"::{645FF040-5081-101B-9F08-00AA002F954E}", CSIDL_BITBUCKET);
}

static VOID LS_StripLnk(LPWSTR pszName)
{
    SIZE_T cch = wcslen(pszName);
    if (cch > 4 && _wcsicmp(pszName + cch - 4, L".lnk") == 0)
        pszName[cch - 4] = UNICODE_NULL;
}

static VOID LS_ScanPrograms(LPCWSTR pszDir, INT depth)
{
    WCHAR szPattern[MAX_PATH], szPath[MAX_PATH];
    WIN32_FIND_DATAW fd;
    HANDLE hFind;

    if (depth > 3 || FAILED(StringCchPrintfW(szPattern, _countof(szPattern), L"%s\\*", pszDir)))
        return;

    hFind = FindFirstFileW(szPattern, &fd);
    if (hFind == INVALID_HANDLE_VALUE)
        return;

    do
    {
        if (fd.cFileName[0] == L'.')
            continue;
        if (FAILED(StringCchPrintfW(szPath, _countof(szPath), L"%s\\%s", pszDir, fd.cFileName)))
            continue;

        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
        {
            LS_ScanPrograms(szPath, depth + 1);
        }
        else if (g_cApps < LS_MAX_APPS)
        {
            WCHAR szName[MAX_PATH];
            SIZE_T cch = wcslen(fd.cFileName);
            INT i;
            BOOL bDup = FALSE;

            if (cch < 5 || _wcsicmp(fd.cFileName + cch - 4, L".lnk") != 0)
                continue;
            StringCchCopyW(szName, _countof(szName), fd.cFileName);
            LS_StripLnk(szName);
            if (StrStrIW(szName, L"uninstall"))
                continue;
            for (i = 0; i < g_cApps && !bDup; i++)
                bDup = (_wcsicmp(g_Apps[i].szName, szName) == 0);
            if (bDup)
                continue;

            LS_ITEM *pItem = &g_Apps[g_cApps++];
            ZeroMemory(pItem, sizeof(*pItem));
            StringCchCopyW(pItem->szName, _countof(pItem->szName), szName);
            StringCchCopyW(pItem->szPath, _countof(pItem->szPath), szPath);
            LS_LoadIcons(pItem, NULL);
        }
    } while (FindNextFileW(hFind, &fd));

    FindClose(hFind);
}

static int __cdecl LS_CompareApps(const void *a, const void *b)
{
    return _wcsicmp(((const LS_ITEM *)a)->szName, ((const LS_ITEM *)b)->szName);
}

static VOID LS_LoadApps(VOID)
{
    WCHAR szDir[MAX_PATH];
    INT i;

    if (!g_Apps)
    {
        g_Apps = (LS_ITEM *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(LS_ITEM) * LS_MAX_APPS);
        if (!g_Apps)
            return;
    }

    for (i = 0; i < g_cApps; i++)
        LS_FreeItem(&g_Apps[i]);
    g_cApps = 0;

    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_PROGRAMS, NULL, SHGFP_TYPE_CURRENT, szDir)))
        LS_ScanPrograms(szDir, 0);
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_COMMON_PROGRAMS, NULL, SHGFP_TYPE_CURRENT, szDir)))
        LS_ScanPrograms(szDir, 0);

    qsort(g_Apps, g_cApps, sizeof(LS_ITEM), LS_CompareApps);
}

static VOID LS_LoadRecent(VOID)
{
    WCHAR szDir[MAX_PATH], szPattern[MAX_PATH];
    WIN32_FIND_DATAW fd;
    FILETIME ftTimes[LS_MAX_RECENT];
    HANDLE hFind;
    INT i, j;

    for (i = 0; i < g_cRecent; i++)
        LS_FreeItem(&g_Recent[i]);
    g_cRecent = 0;

    if (FAILED(SHGetFolderPathW(NULL, CSIDL_RECENT, NULL, SHGFP_TYPE_CURRENT, szDir)) ||
        FAILED(StringCchPrintfW(szPattern, _countof(szPattern), L"%s\\*.lnk", szDir)))
    {
        return;
    }

    hFind = FindFirstFileW(szPattern, &fd);
    if (hFind == INVALID_HANDLE_VALUE)
        return;

    do
    {
        /* Keep the newest LS_MAX_RECENT entries, sorted newest first */
        for (i = 0; i < g_cRecent; i++)
        {
            if (CompareFileTime(&fd.ftLastWriteTime, &ftTimes[i]) > 0)
                break;
        }
        if (i >= LS_MAX_RECENT)
            continue;

        if (g_cRecent == LS_MAX_RECENT)
            LS_FreeItem(&g_Recent[LS_MAX_RECENT - 1]);
        else
            g_cRecent++;

        for (j = g_cRecent - 1; j > i; j--)
        {
            g_Recent[j] = g_Recent[j - 1];
            ftTimes[j] = ftTimes[j - 1];
        }

        ZeroMemory(&g_Recent[i], sizeof(g_Recent[i]));
        ftTimes[i] = fd.ftLastWriteTime;
        StringCchCopyW(g_Recent[i].szName, _countof(g_Recent[i].szName), fd.cFileName);
        LS_StripLnk(g_Recent[i].szName);
        StringCchPrintfW(g_Recent[i].szPath, _countof(g_Recent[i].szPath), L"%s\\%s", szDir, fd.cFileName);
        LS_LoadIcons(&g_Recent[i], NULL);
    } while (FindNextFileW(hFind, &fd));

    FindClose(hFind);
}

static VOID LS_UpdateFilter(VOID)
{
    WCHAR szQuery[MAX_PATH];
    INT i;

    g_cFiltered = 0;
    GetWindowTextW(g_hwndSearch, szQuery, _countof(szQuery));
    StrTrimW(szQuery, L" ");

    for (i = 0; i < g_cApps && g_cFiltered < LS_MAX_APPS; i++)
    {
        if (!szQuery[0] || StrStrIW(g_Apps[i].szName, szQuery))
            g_Filtered[g_cFiltered++] = i;
    }

    if (szQuery[0])
        g_View = LSV_SEARCH;
    else if (g_View == LSV_SEARCH)
        g_View = LSV_HOME;
    g_Scroll = 0;
}

/* ---------------------------------------------------------------- actions */

static VOID LS_Hide(VOID)
{
    if (g_hwndMenu && IsWindowVisible(g_hwndMenu))
    {
        ShowWindow(g_hwndMenu, SW_HIDE);
        g_dwHiddenTick = GetTickCount();
    }
}

static VOID LS_Launch(const LS_ITEM *pItem)
{
    LS_Hide();
    ShellExecuteW(NULL, L"open", pItem->szPath, pItem->szArgs[0] ? pItem->szArgs : NULL, NULL, SW_SHOWNORMAL);
}

static VOID LS_Activate(INT iHit)
{
    if (iHit < 0 || iHit >= g_cHits)
        return;

    const LS_HITRECT *pHit = &g_Hits[iHit];
    switch (pHit->kind)
    {
        case LSH_PIN:
            LS_Launch(&g_Pins[pHit->index]);
            break;
        case LSH_RECENT:
            LS_Launch(&g_Recent[pHit->index]);
            break;
        case LSH_APP:
            LS_Launch(&g_Apps[pHit->index]);
            break;
        case LSH_ALLAPPS:
            g_View = LSV_ALLAPPS;
            g_Scroll = 0;
            InvalidateRect(g_hwndMenu, NULL, FALSE);
            break;
        case LSH_BACK:
            g_View = LSV_HOME;
            SetWindowTextW(g_hwndSearch, L"");
            InvalidateRect(g_hwndMenu, NULL, FALSE);
            break;
        case LSH_POWER:
            LS_Hide();
            PostMessageW(g_hwndTray, TWM_DOEXITWINDOWS, 0, 0);
            break;
        case LSH_USER:
        {
            WCHAR szProfile[MAX_PATH];
            LS_Hide();
            if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_PROFILE, NULL, SHGFP_TYPE_CURRENT, szProfile)))
                ShellExecuteW(NULL, L"open", szProfile, NULL, NULL, SW_SHOWNORMAL);
            break;
        }
        default:
            break;
    }
}

/* ---------------------------------------------------------------- drawing */

static VOID LS_AddHit(const RECT *prc, LS_HIT kind, INT index)
{
    if (g_cHits >= LS_MAX_HITS)
        return;
    g_Hits[g_cHits].rc = *prc;
    g_Hits[g_cHits].kind = kind;
    g_Hits[g_cHits].index = index;
    g_cHits++;
}

static VOID LS_FillRound(HDC hdc, const RECT *prc, COLORREF clrFill, COLORREF clrBorder, INT radius)
{
    HBRUSH hbr = CreateSolidBrush(clrFill);
    HPEN hpen = CreatePen(PS_SOLID, 1, clrBorder);
    HGDIOBJ hbrOld = SelectObject(hdc, hbr);
    HGDIOBJ hpenOld = SelectObject(hdc, hpen);
    RoundRect(hdc, prc->left, prc->top, prc->right, prc->bottom, radius * 2, radius * 2);
    SelectObject(hdc, hbrOld);
    SelectObject(hdc, hpenOld);
    DeleteObject(hbr);
    DeleteObject(hpen);
}

static VOID LS_Text(HDC hdc, LPCWSTR psz, RECT rc, HFONT hFont, COLORREF clr, UINT uFormat)
{
    HGDIOBJ hOld = SelectObject(hdc, hFont);
    SetTextColor(hdc, clr);
    SetBkMode(hdc, TRANSPARENT);
    DrawTextW(hdc, psz, -1, &rc, uFormat | DT_NOPREFIX | DT_END_ELLIPSIS);
    SelectObject(hdc, hOld);
}

static BOOL LS_IsHot(INT iHitIndex)
{
    return iHitIndex == g_iHot;
}

/* Draws a pill-shaped text button and registers it for hit testing */
static VOID LS_Button(HDC hdc, RECT rc, LPCWSTR pszText, LS_HIT kind)
{
    INT iHit = g_cHits;
    LS_AddHit(&rc, kind, 0);
    LS_FillRound(hdc, &rc, LS_IsHot(iHit) ? CLR_HOVER : RGB(251, 251, 251), CLR_SEARCH_BORDER, 4);
    LS_Text(hdc, pszText, rc, g_hFontSmall, CLR_TEXT, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
}

static VOID LS_DrawList(HDC hdc, INT yTop, INT yBottom, const INT *pIndices, INT cIndices)
{
    HRGN hrgn = CreateRectRgn(LS_MARGIN - 8, yTop, LS_WIDTH - LS_MARGIN + 8, yBottom);
    INT i, cyTotal = cIndices * LS_LIST_ROW_H;
    INT maxScroll = max(0, cyTotal - (yBottom - yTop));

    g_Scroll = max(0, min(g_Scroll, maxScroll));
    SelectClipRgn(hdc, hrgn);

    for (i = 0; i < cIndices; i++)
    {
        RECT rc;
        INT y = yTop + i * LS_LIST_ROW_H - g_Scroll;
        const LS_ITEM *pItem = &g_Apps[pIndices[i]];

        if (y + LS_LIST_ROW_H < yTop || y > yBottom)
            continue;

        SetRect(&rc, LS_MARGIN, y, LS_WIDTH - LS_MARGIN, y + LS_LIST_ROW_H - 2);
        INT iHit = g_cHits;
        RECT rcHit = rc;
        rcHit.top = max(rc.top, (LONG)yTop);
        rcHit.bottom = min(rc.bottom, (LONG)yBottom);
        LS_AddHit(&rcHit, LSH_APP, pIndices[i]);

        if (LS_IsHot(iHit) || (g_View == LSV_SEARCH && i == 0))
            LS_FillRound(hdc, &rc, CLR_HOVER, CLR_HOVER, 4);
        if (pItem->hIconSmall)
            DrawIconEx(hdc, rc.left + 12, y + (LS_LIST_ROW_H - 18) / 2, pItem->hIconSmall, 16, 16, 0, NULL, DI_NORMAL);

        rc.left += 44;
        LS_Text(hdc, pItem->szName, rc, g_hFont, CLR_TEXT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
    }

    if (!cIndices)
    {
        RECT rc = { LS_MARGIN, yTop + 8, LS_WIDTH - LS_MARGIN, yTop + 40 };
        LS_Text(hdc, L"No results", rc, g_hFont, CLR_TEXT_DIM, DT_LEFT | DT_SINGLELINE);
    }

    SelectClipRgn(hdc, NULL);
    DeleteObject(hrgn);
}

static VOID LS_DrawPowerGlyph(HDC hdc, INT cx, INT cy)
{
    HPEN hpen = CreatePen(PS_SOLID, 2, CLR_TEXT);
    HGDIOBJ hOld = SelectObject(hdc, hpen);
    HGDIOBJ hbrOld = SelectObject(hdc, GetStockObject(NULL_BRUSH));
    /* open circle with a gap at the top, plus the vertical stroke */
    Arc(hdc, cx - 8, cy - 7, cx + 9, cy + 10, cx + 4, cy - 6, cx - 4, cy - 6);
    MoveToEx(hdc, cx, cy - 9, NULL);
    LineTo(hdc, cx, cy + 1);
    SelectObject(hdc, hbrOld);
    SelectObject(hdc, hOld);
    DeleteObject(hpen);
}

static VOID LS_DrawSearchGlyph(HDC hdc, INT x, INT y)
{
    HPEN hpen = CreatePen(PS_SOLID, 2, CLR_TEXT_DIM);
    HGDIOBJ hOld = SelectObject(hdc, hpen);
    HGDIOBJ hbrOld = SelectObject(hdc, GetStockObject(NULL_BRUSH));
    Ellipse(hdc, x, y, x + 11, y + 11);
    MoveToEx(hdc, x + 10, y + 10, NULL);
    LineTo(hdc, x + 15, y + 15);
    SelectObject(hdc, hbrOld);
    SelectObject(hdc, hOld);
    DeleteObject(hpen);
}

static VOID LS_Paint(HDC hdc)
{
    RECT rc, rcClient = { 0, 0, LS_WIDTH, g_Height };
    INT i, y, yBottomBar = g_Height - LS_BOTTOM_H;
    HBRUSH hbr;

    g_cHits = 0;

    /* background and border */
    hbr = CreateSolidBrush(CLR_BG);
    FillRect(hdc, &rcClient, hbr);
    DeleteObject(hbr);

    /* search box (the edit control lives inside it) */
    SetRect(&rc, LS_MARGIN, LS_MARGIN, LS_WIDTH - LS_MARGIN, LS_MARGIN + 36);
    LS_FillRound(hdc, &rc, CLR_SEARCH_BG, CLR_SEARCH_BORDER, 18);
    LS_DrawSearchGlyph(hdc, rc.left + 16, rc.top + 10);

    y = LS_MARGIN + 36 + 24;

    if (g_View == LSV_HOME)
    {
        /* Pinned */
        SetRect(&rc, LS_MARGIN + 8, y, LS_WIDTH / 2, y + 24);
        LS_Text(hdc, L"Pinned", rc, g_hFontBold, CLR_TEXT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
        SetRect(&rc, LS_WIDTH - LS_MARGIN - 96, y, LS_WIDTH - LS_MARGIN - 8, y + 24);
        LS_Button(hdc, rc, L"All apps  >", LSH_ALLAPPS);
        y += 36;

        INT cellW = (LS_WIDTH - 2 * LS_MARGIN) / LS_COLS;
        INT cRows = (g_cPins + LS_COLS - 1) / LS_COLS;
        for (i = 0; i < g_cPins; i++)
        {
            RECT rcCell;
            INT col = i % LS_COLS, row = i / LS_COLS;
            SetRect(&rcCell, LS_MARGIN + col * cellW + 2, y + row * LS_CELL_H,
                    LS_MARGIN + (col + 1) * cellW - 2, y + (row + 1) * LS_CELL_H - 4);
            INT iHit = g_cHits;
            LS_AddHit(&rcCell, LSH_PIN, i);
            if (LS_IsHot(iHit))
                LS_FillRound(hdc, &rcCell, CLR_HOVER, CLR_HOVER, 4);
            if (g_Pins[i].hIcon)
                DrawIconEx(hdc, (rcCell.left + rcCell.right) / 2 - 16, rcCell.top + 10, g_Pins[i].hIcon, 32, 32, 0, NULL, DI_NORMAL);
            rc = rcCell;
            rc.top += 48;
            rc.left += 2;
            rc.right -= 2;
            LS_Text(hdc, g_Pins[i].szName, rc, g_hFontSmall, CLR_TEXT, DT_CENTER | DT_TOP | DT_SINGLELINE);
        }
        y += cRows * LS_CELL_H + 12;

        /* Recommended (recent files), as many rows as fit */
        INT cRecRows = (yBottomBar - (y + 32) - 8) / LS_REC_ROW_H;
        if (cRecRows > 0)
        {
            SetRect(&rc, LS_MARGIN + 8, y, LS_WIDTH / 2, y + 24);
            LS_Text(hdc, L"Recommended", rc, g_hFontBold, CLR_TEXT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            y += 32;

            if (!g_cRecent)
            {
                SetRect(&rc, LS_MARGIN + 8, y, LS_WIDTH - LS_MARGIN, y + 24);
                LS_Text(hdc, L"Files you open recently will show up here.", rc, g_hFont, CLR_TEXT_DIM,
                        DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            }

            INT halfW = (LS_WIDTH - 2 * LS_MARGIN) / 2;
            for (i = 0; i < g_cRecent && i / 2 < min(cRecRows, 3); i++)
            {
                RECT rcCell;
                INT col = i % 2, row = i / 2;
                SetRect(&rcCell, LS_MARGIN + col * halfW, y + row * LS_REC_ROW_H,
                        LS_MARGIN + (col + 1) * halfW - 6, y + (row + 1) * LS_REC_ROW_H - 4);
                INT iHit = g_cHits;
                LS_AddHit(&rcCell, LSH_RECENT, i);
                if (LS_IsHot(iHit))
                    LS_FillRound(hdc, &rcCell, CLR_HOVER, CLR_HOVER, 4);
                if (g_Recent[i].hIcon)
                    DrawIconEx(hdc, rcCell.left + 8, rcCell.top + 8, g_Recent[i].hIcon, 32, 32, 0, NULL, DI_NORMAL);
                rc = rcCell;
                rc.left += 50;
                LS_Text(hdc, g_Recent[i].szName, rc, g_hFont, CLR_TEXT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            }
        }
    }
    else
    {
        SetRect(&rc, LS_MARGIN + 8, y, LS_WIDTH / 2, y + 24);
        LS_Text(hdc, g_View == LSV_SEARCH ? L"Best matches" : L"All apps", rc, g_hFontBold, CLR_TEXT,
                DT_LEFT | DT_VCENTER | DT_SINGLELINE);
        SetRect(&rc, LS_WIDTH - LS_MARGIN - 80, y, LS_WIDTH - LS_MARGIN - 8, y + 24);
        LS_Button(hdc, rc, L"<  Back", LSH_BACK);
        y += 36;
        LS_DrawList(hdc, y, yBottomBar - 8, g_Filtered, g_cFiltered);
    }

    /* bottom bar: user and power */
    SetRect(&rc, 0, yBottomBar, LS_WIDTH, g_Height);
    hbr = CreateSolidBrush(CLR_BOTTOM);
    FillRect(hdc, &rc, hbr);
    DeleteObject(hbr);
    {
        HPEN hpen = CreatePen(PS_SOLID, 1, CLR_BORDER);
        HGDIOBJ hOld = SelectObject(hdc, hpen);
        MoveToEx(hdc, 0, yBottomBar, NULL);
        LineTo(hdc, LS_WIDTH, yBottomBar);
        SelectObject(hdc, hOld);
        DeleteObject(hpen);
    }

    RECT rcUser = { LS_MARGIN + 16, yBottomBar + 12, LS_MARGIN + 16 + 220, g_Height - 12 };
    INT iHitUser = g_cHits;
    LS_AddHit(&rcUser, LSH_USER, 0);
    if (LS_IsHot(iHitUser))
        LS_FillRound(hdc, &rcUser, CLR_HOVER, CLR_HOVER, 4);
    {
        /* avatar: accent circle with the user's initial */
        RECT rcAvatar = { rcUser.left + 6, rcUser.top + 4, rcUser.left + 38, rcUser.top + 36 };
        HBRUSH hbrA = CreateSolidBrush(CLR_ACCENT);
        HGDIOBJ hbrOld = SelectObject(hdc, hbrA);
        HGDIOBJ hpenOld = SelectObject(hdc, GetStockObject(NULL_PEN));
        Ellipse(hdc, rcAvatar.left, rcAvatar.top, rcAvatar.right + 1, rcAvatar.bottom + 1);
        SelectObject(hdc, hbrOld);
        SelectObject(hdc, hpenOld);
        DeleteObject(hbrA);
        WCHAR szInitial[2] = { (WCHAR)CharUpperW((LPWSTR)(ULONG_PTR)g_szUser[0]), 0 };
        LS_Text(hdc, szInitial, rcAvatar, g_hFontBold, RGB(255, 255, 255), DT_CENTER | DT_VCENTER | DT_SINGLELINE);
        rc = rcUser;
        rc.left = rcAvatar.right + 12;
        LS_Text(hdc, g_szUser, rc, g_hFont, CLR_TEXT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
    }

    RECT rcPower = { LS_WIDTH - LS_MARGIN - 52, yBottomBar + 12, LS_WIDTH - LS_MARGIN - 12, g_Height - 12 };
    INT iHitPower = g_cHits;
    LS_AddHit(&rcPower, LSH_POWER, 0);
    if (LS_IsHot(iHitPower))
        LS_FillRound(hdc, &rcPower, CLR_HOVER, CLR_HOVER, 4);
    LS_DrawPowerGlyph(hdc, (rcPower.left + rcPower.right) / 2, (rcPower.top + rcPower.bottom) / 2);

    /* outer border */
    {
        HPEN hpen = CreatePen(PS_SOLID, 1, CLR_BORDER);
        HGDIOBJ hOld = SelectObject(hdc, hpen);
        HGDIOBJ hbrOld = SelectObject(hdc, GetStockObject(NULL_BRUSH));
        RoundRect(hdc, 0, 0, LS_WIDTH, g_Height, 16, 16);
        SelectObject(hdc, hbrOld);
        SelectObject(hdc, hOld);
        DeleteObject(hpen);
    }
}

static INT LS_HitTest(POINT pt)
{
    INT i;
    for (i = 0; i < g_cHits; i++)
    {
        if (PtInRect(&g_Hits[i].rc, pt))
            return i;
    }
    return -1;
}

/* ------------------------------------------------------------ window procs */

static LRESULT CALLBACK LS_EditProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    switch (uMsg)
    {
        case WM_KEYDOWN:
            if (wParam == VK_ESCAPE)
            {
                if (GetWindowTextLengthW(hwnd) > 0)
                    SetWindowTextW(hwnd, L"");
                else
                    LS_Hide();
                return 0;
            }
            if (wParam == VK_RETURN)
            {
                if (g_View == LSV_SEARCH && g_cFiltered > 0)
                    LS_Launch(&g_Apps[g_Filtered[0]]);
                return 0;
            }
            break;

        case WM_CHAR:
            if (wParam == VK_RETURN || wParam == VK_ESCAPE)
                return 0;
            break;

        case WM_PAINT:
        {
            LRESULT lr = CallWindowProcW(g_pfnEditProc, hwnd, uMsg, wParam, lParam);
            if (GetWindowTextLengthW(hwnd) == 0)
            {
                /* placeholder text */
                HDC hdc = GetDC(hwnd);
                RECT rc;
                GetClientRect(hwnd, &rc);
                rc.left += 2;
                LS_Text(hdc, L"Type here to search", rc, g_hFont, CLR_TEXT_DIM, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
                ReleaseDC(hwnd, hdc);
            }
            return lr;
        }
    }
    return CallWindowProcW(g_pfnEditProc, hwnd, uMsg, wParam, lParam);
}

static LRESULT CALLBACK LS_WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    switch (uMsg)
    {
        case WM_CREATE:
            g_hwndSearch = CreateWindowExW(0, L"EDIT", L"",
                                           WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
                                           LS_MARGIN + 44, LS_MARGIN + 10, LS_WIDTH - 2 * LS_MARGIN - 60, 18,
                                           hwnd, (HMENU)IDC_LS_SEARCH, hExplorerInstance, NULL);
            SendMessageW(g_hwndSearch, WM_SETFONT, (WPARAM)g_hFont, FALSE);
            g_pfnEditProc = (WNDPROC)SetWindowLongPtrW(g_hwndSearch, GWLP_WNDPROC, (LONG_PTR)LS_EditProc);
            return 0;

        case WM_ERASEBKGND:
            return 1;

        case WM_PAINT:
        {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            HDC hdcMem = CreateCompatibleDC(hdc);
            HBITMAP hbm = CreateCompatibleBitmap(hdc, LS_WIDTH, g_Height);
            HGDIOBJ hOld = SelectObject(hdcMem, hbm);
            LS_Paint(hdcMem);
            BitBlt(hdc, 0, 0, LS_WIDTH, g_Height, hdcMem, 0, 0, SRCCOPY);
            SelectObject(hdcMem, hOld);
            DeleteObject(hbm);
            DeleteDC(hdcMem);
            EndPaint(hwnd, &ps);
            return 0;
        }

        case WM_CTLCOLOREDIT:
            SetBkColor((HDC)wParam, CLR_SEARCH_BG);
            SetTextColor((HDC)wParam, CLR_TEXT);
            return (LRESULT)GetStockObject(WHITE_BRUSH);

        case WM_COMMAND:
            if (LOWORD(wParam) == IDC_LS_SEARCH && HIWORD(wParam) == EN_CHANGE)
            {
                LS_UpdateFilter();
                g_iHot = -1;
                InvalidateRect(hwnd, NULL, FALSE);
            }
            return 0;

        case WM_MOUSEMOVE:
        {
            POINT pt = { GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) };
            INT iHot = LS_HitTest(pt);
            if (iHot != g_iHot)
            {
                g_iHot = iHot;
                InvalidateRect(hwnd, NULL, FALSE);
            }
            TRACKMOUSEEVENT tme = { sizeof(tme), TME_LEAVE, hwnd, 0 };
            TrackMouseEvent(&tme);
            return 0;
        }

        case WM_MOUSELEAVE:
            if (g_iHot != -1)
            {
                g_iHot = -1;
                InvalidateRect(hwnd, NULL, FALSE);
            }
            return 0;

        case WM_LBUTTONUP:
        {
            POINT pt = { GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) };
            LS_Activate(LS_HitTest(pt));
            return 0;
        }

        case WM_MOUSEWHEEL:
            if (g_View != LSV_HOME)
            {
                g_Scroll -= (GET_WHEEL_DELTA_WPARAM(wParam) / WHEEL_DELTA) * LS_LIST_ROW_H * 3;
                g_iHot = -1;
                InvalidateRect(hwnd, NULL, FALSE);
            }
            return 0;

        case WM_ACTIVATE:
            if (LOWORD(wParam) == WA_INACTIVE)
                LS_Hide();
            else
                SetFocus(g_hwndSearch);
            return 0;
    }
    return DefWindowProcW(hwnd, uMsg, wParam, lParam);
}

static BOOL LS_Create(VOID)
{
    WNDCLASSEXW wc = { sizeof(wc) };
    DWORD cchUser = _countof(g_szUser);

    if (g_hwndMenu)
        return TRUE;

    g_hFont = CreateFontW(-12, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"Selawik");
    g_hFontSmall = CreateFontW(-11, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"Selawik");
    g_hFontBold = CreateFontW(-13, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"Selawik");

    if (!GetUserNameW(g_szUser, &cchUser))
        StringCchCopyW(g_szUser, _countof(g_szUser), L"User");

    wc.lpfnWndProc = LS_WndProc;
    wc.hInstance = hExplorerInstance;
    wc.hCursor = LoadCursorW(NULL, IDC_ARROW);
    wc.lpszClassName = LS_CLASSNAME;
    wc.style = CS_DROPSHADOW;
    RegisterClassExW(&wc);

    g_hwndMenu = CreateWindowExW(WS_EX_TOOLWINDOW | WS_EX_TOPMOST, LS_CLASSNAME, L"Start",
                                 WS_POPUP | WS_CLIPCHILDREN, 0, 0, LS_WIDTH, LS_MAXHEIGHT,
                                 NULL, NULL, hExplorerInstance, NULL);
    return g_hwndMenu != NULL;
}

/* ------------------------------------------------------------------- API */

BOOL LumenStart_IsVisible(VOID)
{
    return g_hwndMenu && IsWindowVisible(g_hwndMenu);
}

VOID LumenStart_Hide(VOID)
{
    LS_Hide();
}

VOID LumenStart_Toggle(HWND hwndTray, const RECT *prcStartButton, BOOL bTaskbarAtTop)
{
    MONITORINFO mi = { sizeof(mi) };
    POINT pt;
    INT x, y;

    if (LumenStart_IsVisible())
    {
        LS_Hide();
        return;
    }

    /* A click on the start button first deactivates (and hides) the menu;
       don't reopen it right away in that case. */
    GetCursorPos(&pt);
    if (GetTickCount() - g_dwHiddenTick < 300 && PtInRect(prcStartButton, pt))
        return;

    g_hwndTray = hwndTray;
    g_rcStartButton = *prcStartButton;
    if (!LS_Create())
        return;

    LS_LoadPins();
    LS_LoadApps();
    LS_LoadRecent();

    GetMonitorInfoW(MonitorFromRect(prcStartButton, MONITOR_DEFAULTTONEAREST), &mi);
    g_Height = min(LS_MAXHEIGHT, (INT)(mi.rcWork.bottom - mi.rcWork.top) - 2 * LS_GAP);

    x = (mi.rcMonitor.left + mi.rcMonitor.right - LS_WIDTH) / 2;
    x = max((INT)mi.rcWork.left + LS_GAP, min(x, (INT)mi.rcWork.right - LS_WIDTH - LS_GAP));
    y = bTaskbarAtTop ? mi.rcWork.top + LS_GAP : mi.rcWork.bottom - g_Height - LS_GAP;

    g_View = LSV_HOME;
    g_Scroll = 0;
    g_iHot = -1;
    SetWindowTextW(g_hwndSearch, L"");
    LS_UpdateFilter();

    SetWindowPos(g_hwndMenu, HWND_TOPMOST, x, y, LS_WIDTH, g_Height, SWP_NOACTIVATE);
    SetWindowRgn(g_hwndMenu, CreateRoundRectRgn(0, 0, LS_WIDTH + 1, g_Height + 1, 16, 16), FALSE);
    ShowWindow(g_hwndMenu, SW_SHOW);
    SetForegroundWindow(g_hwndMenu);
    SetFocus(g_hwndSearch);
    InvalidateRect(g_hwndMenu, NULL, TRUE);
}
