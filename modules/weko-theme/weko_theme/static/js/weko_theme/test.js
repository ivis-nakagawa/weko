
(function () {
    const test_func = () => {
        console.log('test_func');
    }
    var urlEscapes = {
        ';': '%3B',
        ',': '%2C',
        '/': '%2F',
        '?': '%3F',
        ':': '%3A',
        '@': '%40',
        '&': '%26',
        '=': '%3D',
        '+': '%2B',
        '$': '%24',
        '#': '%23',
    };
    var regexUrlEscapes = new RegExp(
        '[' + Object.keys(urlEscapes).join('') + ']', 'g'
    );
    var regexUrlUnescapes = new RegExp(
        Object.values(urlEscapes).join('|'), 'g'
    );

    /**
     * ファイル名に「#」が含まれるとURLが途切れる問題の対策(#48298参照)
     * ファイル名に含まれた予約文字をエスケープする
     * encodeURIでエンコードされない記号のみをエスケープ対象とする(日本語等は変換しない)
     * TODO: モジュールアップデート後に修正が必要
     * @param {string} fileName エスケープ処理対象の文字列
     * @returns {string} エスケープ処理が行われた文字列
     */
    const escapeFileName = function (fileName) {
        if (typeof fileName === 'string' && fileName.length > 0) {
            fileName = fileName.replace(regexUrlEscapes, function (c) {
                return urlEscapes[c];
            });
        }
        return fileName;
    }

    /**
     * ファイル名に「#」が含まれるとURLが途切れる問題の対策(#48298参照)
     * escapeFileNameでエスケープされた予約文字を元に戻す
     * TODO: モジュールアップデート後に修正が必要
     * @param {string} fileName アンエスケープ処理対象の文字列
     * @returns {string} アンエスケープ処理が行われた文字列
     */
    const unescapeFileName = function (fileName) {
        if (typeof fileName === 'string' && fileName.length > 0) {
            fileName = fileName.replace(regexUrlUnescapes, function (c) {
                return Object.keys(urlEscapes).find(key => urlEscapes[key] === c);
            });
        }
        return fileName;
    }

    /**
     * データに「{{}}」が含まれるとエラーが発生する問題の対策(#46627参照)
     * 一時的に入れたゼロ幅スペースを削除する
     * TODO: モジュールアップデート後に修正が必要
     * @param {*} data ゼロ幅スペースの削除処理対象のデータ
     * @returns ゼロ幅スペースを削除したデータ
     */
    const replaceZeroWidthSpace = function (data) {
        if (data !== null) {
            if (Array.isArray(data)) {
                return data.map(item => replaceZeroWidthSpace(item));
            } else if (typeof data === 'object') {
                let newRecord = {};
                Object.entries(data).forEach(([key, value]) => {
                    newRecord[key] = replaceZeroWidthSpace(value);
                });
                return newRecord;
            } else if (typeof data === 'string') {
                return data.replace(/\u200b/g, '');
            }
        }
        return data;
    }

    const removeWeko2SpecialCharacter = function (data) {
        if (typeof data === 'string' && data.length > 0) {
            data = data
            .replace(/(^(&EMPTY&,|,&EMPTY&)|(&EMPTY&,|,&EMPTY&)$|&EMPTY&)/g, "")
            .trim();
            return data === ',' ? '' : data;
        }
        return data;
    }

    if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
        module.exports = {
            test_func,
            replaceZeroWidthSpace,
            escapeFileName,
            unescapeFileName,
            removeWeko2SpecialCharacter,
        };
    } else {
        window.test_func = test_func;
        window.replaceZeroWidthSpace = replaceZeroWidthSpace;
        window.escapeFileName = escapeFileName;
        window.unescapeFileName = unescapeFileName;
        window.removeWeko2SpecialCharacter = removeWeko2SpecialCharacter;
    }
})();
