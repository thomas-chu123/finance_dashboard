import { computed, ref, watch } from 'vue'
import zhTW from '../locales/zh-TW.json'
import en from '../locales/en.json'
import ja from '../locales/ja.json'

const STORAGE_KEY = 'nexus-locale'
const DEFAULT_LOCALE = 'zh-TW'
const messages = { 'zh-TW': zhTW, en, ja }
const supportedLocales = [
  { code: 'zh-TW', labelKey: 'language.zhTW' },
  { code: 'en', labelKey: 'language.en' },
  { code: 'ja', labelKey: 'language.ja' },
]

const savedLocale = window.localStorage.getItem(STORAGE_KEY)
const locale = ref(messages[savedLocale] ? savedLocale : DEFAULT_LOCALE)

function getValue(object, path) {
  return path.split('.').reduce((value, key) => value?.[key], object)
}

/** 提供 UI 語系選擇與 JSON 翻譯查詢。 */
export function useLocale() {
  const t = (key) => getValue(messages[locale.value], key) ?? getValue(messages[DEFAULT_LOCALE], key) ?? key

  const languageName = computed(() => t(supportedLocales.find(item => item.code === locale.value)?.labelKey))

  function setLocale(nextLocale) {
    if (messages[nextLocale]) locale.value = nextLocale
  }

  watch(locale, (nextLocale) => {
    window.localStorage.setItem(STORAGE_KEY, nextLocale)
    document.documentElement.lang = nextLocale
  }, { immediate: true })

  return { locale, supportedLocales, languageName, setLocale, t }
}

export const translate = (key) => getValue(messages[locale.value], key) ?? getValue(messages[DEFAULT_LOCALE], key) ?? key

/** Return an asset name appropriate for the active UI language. */
export const localizedName = (item) => {
  if (!item) return ''
  if (item.category === 'jp_etf') {
    return locale.value === 'en'
      ? (item.name_en || item.name || item.name_ja || item.symbol)
      : (item.name_ja || item.name_zh || item.name || item.name_en || item.symbol)
  }
  return item.name || item.name_en || item.name_zh || item.name_ja || item.symbol || ''
}
