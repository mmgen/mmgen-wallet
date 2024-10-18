#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
mn_entry.py - Mnemonic user entry methods for the MMGen suite
"""

import sys, time

from .util import msg, msg_r, fmt, fmt_list, capfirst, die, ascii_lowercase
from .term import get_char, get_char_raw
from .color import cyan

_return_chars = '\n\r '
_erase_chars = '\b\x7f'

class MnEntryMode:
	"""
	Subclasses must implement:
	  - pad_max:    pad character limit (None if variable)
	  - ss_len:     substring length for automatic entry
	  - get_word(): get a word from the user and return an index into the wordlist,
	                or None on failure
	"""

	pad_max_info = """
		Up to {pad_max}
		pad characters per word are permitted.
	"""

	def __init__(self, mne):
		self.pad_max_info = '  ' + self.pad_max_info.lstrip() if self.pad_max else '\n'
		self.mne = mne

	def get_char(self, s):
		did_erase = False
		while True:
			ch = get_char_raw('', num_bytes=1)
			if s and ch in _erase_chars:
				s = s[:-1]
				did_erase = True
			else:
				return (ch, s, did_erase)

class MnEntryModeFull(MnEntryMode):
	name = 'Full'
	choose_info = """
		Words must be typed in full and entered with ENTER, SPACE,
		or a pad character.
	"""
	prompt_info = """
		Use the ENTER or SPACE key to enter each word.  A pad character will also
		enter a word once you’ve typed {ssl} characters total (including pad chars).
	"""
	pad_max = None

	@property
	def ss_len(self):
		return self.mne.longest_word

	def get_word(self, mne):
		s, pad = ('', 0)
		while True:
			ch, s, _ = self.get_char(s)
			if ch in _return_chars:
				if s:
					break
			elif ch in ascii_lowercase:
				s += ch
			else:
				pad += 1
				if pad + len(s) > self.ss_len:
					break

		return mne.idx(s, 'full')

class MnEntryModeShort(MnEntryMode):
	name = 'Short'
	choose_info = """
		Words are entered automatically once {usl} valid word letters
		are typed.
	"""
	prompt_info = """
		Each word is entered automatically once {ssl} valid word letters are typed.
	"""
	prompt_info_bip39_add = """
		Words shorter than {ssl} letters can be entered with ENTER or SPACE, or by
		exceeding the pad character limit.
	"""
	pad_max = 16

	def __init__(self, mne):
		if mne.wl_id == 'bip39':
			self.prompt_info += '  ' + self.prompt_info_bip39_add.strip()
		super().__init__(mne)

	@property
	def ss_len(self):
		return self.mne.uniq_ss_len

	def get_word(self, mne):
		s, pad = ('', 0)
		while True:
			ch, s, _ = self.get_char(s)
			if ch in _return_chars:
				if s:
					break
			elif ch in ascii_lowercase:
				s += ch
				if len(s) == self.ss_len:
					break
			else:
				pad += 1
				if pad > self.pad_max:
					break

		return mne.idx(s, 'short')

class MnEntryModeFixed(MnEntryMode):
	name = 'Fixed'
	choose_info = """
		Words are entered automatically once exactly {usl} characters
		are typed.
	"""
	prompt_info = """
		Each word is entered automatically once exactly {ssl} characters are typed.
	"""
	prompt_info_add = ("""
		Words shorter than {ssl} letters must be padded to fit.
		""", """
		{sw}-letter words must be padded with one pad character.
		""")
	pad_max = None

	def __init__(self, mne):
		self.len_diff = mne.uniq_ss_len - mne.shortest_word
		self.prompt_info += self.prompt_info_add[self.len_diff==1].lstrip()
		super().__init__(mne)

	@property
	def ss_len(self):
		return self.mne.uniq_ss_len

	def get_word(self, mne):
		s, pad = ('', 0)
		while True:
			ch, s, _ = self.get_char(s)
			if ch in _return_chars:
				if s:
					break
			elif ch in ascii_lowercase:
				s += ch
				if len(s) + pad == self.ss_len:
					return mne.idx(s, 'short')
			else:
				pad += 1
				if pad > self.len_diff:
					return None
				if len(s) + pad == self.ss_len:
					return mne.idx(s, 'short')

class MnEntryModeMinimal(MnEntryMode):
	name = 'Minimal'
	choose_info = """
		Words are entered automatically once a minimum number of
		letters are typed (the number varies from word to word).
	"""
	prompt_info = """
		Each word is entered automatically once the minimum required number of valid
		word letters is typed.

		If your word is not entered automatically, that means it’s a substring of
		another word in the wordlist.  Such words must be entered explicitly with
		the ENTER or SPACE key, or by exceeding the pad character limit.
	"""
	pad_max = 16
	ss_len = None

	def get_word(self, mne):
		s, pad = ('', 0)
		lo, hi = (0, len(mne.wl) - 1)
		while True:
			ch, s, did_erase = self.get_char(s)
			if did_erase:
				lo, hi = (0, len(mne.wl) - 1)
			if ch in _return_chars:
				if s:
					return mne.idx(s, 'full', lo_idx=lo, hi_idx=hi)
			elif ch in ascii_lowercase:
				s += ch
				ret = mne.idx(s, 'minimal', lo_idx=lo, hi_idx=hi)
				if not isinstance(ret, tuple):
					return ret
				lo, hi = ret
			else:
				pad += 1
				if pad > self.pad_max:
					return mne.idx(s, 'full', lo_idx=lo, hi_idx=hi)

class MnemonicEntry:

	prompt_info = {
		'intro': """
			You will now be prompted for your {ml}-word seed phrase, one word at a time.
		""",
		'pad_info': """
			Note that anything you type that’s not a lowercase letter will simply be
			ignored.  This feature allows you to guard against acoustic side-channel
			attacks by padding your keyboard entry with “dead characters”.  Pad char-
			acters may be typed before, after, or in the middle of words.
		""",
	}
	word_prompt = ('Enter word #{}: ', 'Incorrect entry. Repeat word #{}: ')
	usr_dfl_entry_mode = None
	_lw = None
	_sw = None
	_usl = None

	def __init__(self, cfg):
		self.cfg = cfg
		self.set_dfl_entry_mode()

	@property
	def longest_word(self):
		if not self._lw:
			self._lw = max(len(w) for w in self.wl)
		return self._lw

	@property
	def shortest_word(self):
		if not self._sw:
			self._sw = min(len(w) for w in self.wl)
		return self._sw

	@property
	def uniq_ss_len(self):
		if not self._usl:
			usl = 0
			for i in range(len(self.wl)-1):
				w1, w2 = self.wl[i], self.wl[i+1]
				while True:
					if w1[:usl] == w2[:usl]:
						usl += 1
					else:
						break
			self._usl = usl
		return self._usl

	def idx(self, w, entry_mode, lo_idx=None, hi_idx=None):
		"""
		Return values:
		  - all modes:
		    - None:            failure (substr not in list)
		    - idx:             success
		  - minimal mode:
		    - (lo_idx,hi_idx): non-unique match
		"""
		trunc_len = {
			'full': self.longest_word,
			'short': self.uniq_ss_len,
			'minimal': len(w),
		}[entry_mode]
		w = w[:trunc_len]
		last_idx = len(self.wl) - 1
		lo = lo_idx or 0
		hi = hi_idx or last_idx
		while True:
			idx = (hi + lo) // 2
			cur_w = self.wl[idx][:trunc_len]
			if cur_w == w:
				if entry_mode == 'minimal':
					if idx > 0 and self.wl[idx-1][:len(w)] == w:
						return (lo, hi)
					elif idx < last_idx and self.wl[idx+1][:len(w)] == w:
						return (lo, hi)
				return idx
			elif hi <= lo:
				return None
			elif cur_w > w:
				hi = idx - 1
			else:
				lo = idx + 1

	def get_cls_by_entry_mode(self, entry_mode):
		return getattr(sys.modules[__name__], 'MnEntryMode' + capfirst(entry_mode))

	def choose_entry_mode(self):
		msg('Choose an entry mode:\n')
		em_objs = [self.get_cls_by_entry_mode(entry_mode)(self) for entry_mode in self.entry_modes]
		for n, mode in enumerate(em_objs, 1):
			msg('  {}) {:8} {}'.format(
				n,
				mode.name + ':',
				fmt(mode.choose_info, ' '*14).lstrip().format(usl=self.uniq_ss_len),
			))
		prompt = f'Type a number, or hit ENTER for the default ({capfirst(self.dfl_entry_mode)}): '
		erase = '\r' + ' ' * (len(prompt)+19) + '\r'
		while True:
			uret = get_char(prompt).strip()
			if uret == '':
				msg_r(erase)
				return self.get_cls_by_entry_mode(self.dfl_entry_mode)(self)
			elif uret in [str(i) for i in range(1, len(em_objs)+1)]:
				msg_r(erase)
				return em_objs[int(uret)-1]
			else:
				msg_r(f'\b {uret!r}: invalid choice ')
				time.sleep(self.cfg.err_disp_timeout)
				msg_r(erase)

	def get_mnemonic_from_user(self, mn_len, validate=True):
		mll = list(self.bconv.seedlen_map_rev)
		assert mn_len in mll, f'{mn_len}: invalid mnemonic length (must be one of {mll})'

		if self.usr_dfl_entry_mode:
			em = self.get_cls_by_entry_mode(self.usr_dfl_entry_mode)(self)
			i_add = ' (user-configured)'
		else:
			em = self.choose_entry_mode()
			i_add = ''

		msg('\r' + f'Using entry mode {cyan(em.name.upper())}{i_add}')
		self.em = em

		if not self.usr_dfl_entry_mode:
			msg('\n' + (
					fmt(self.prompt_info['intro'])
					+ '\n'
					+ fmt(self.prompt_info['pad_info'].rstrip() + em.pad_max_info + em.prompt_info, indent='  ')
				).format(
					ml       = mn_len,
					ssl      = em.ss_len,
					pad_max  = em.pad_max,
					sw       = self.shortest_word,
			))

		clear_line = '\n' if self.cfg.test_suite else '{r}{s}{r}'.format(r='\r', s=' '*40)
		idx, idxs = 1, [] # initialize idx to a non-None value

		while len(idxs) < mn_len:
			msg_r(self.word_prompt[idx is None].format(len(idxs)+1))
			idx = em.get_word(self)
			msg_r(clear_line)
			if idx is None:
				time.sleep(0.1)
			else:
				idxs.append(idx)

		words = [self.wl[i] for i in idxs]

		if validate:
			self.bconv.tohex(words)

		return ' '.join(words)

	@classmethod
	def get_cls_by_wordlist(cls, wl):
		d = {
			'mmgen': MnemonicEntryMMGen,
			'bip39': MnemonicEntryBIP39,
			'xmrseed': MnemonicEntryMonero,
		}
		wl = wl.lower()
		if wl not in d:
			raise ValueError(f'wordlist {wl!r} not recognized (valid choices: {fmt_list(list(d))})')
		return d[wl]

	def set_dfl_entry_mode(self):
		"""
		In addition to setting the default entry mode for the current wordlist, checks validity
		of all user-configured entry modes
		"""
		for k, v in self.cfg.mnemonic_entry_modes.items():
			cls = self.get_cls_by_wordlist(k)
			if v not in cls.entry_modes:
				errmsg = f"""
					Error in cfg file option 'mnemonic_entry_modes':
					Entry mode {v!r} not recognized for wordlist {k!r}:
					Valid choices: {fmt_list(cls.entry_modes)}
				"""
				die(2, '\n' + fmt(errmsg, indent='  '))
			if cls == type(self):
				self.usr_dfl_entry_mode = v

class MnemonicEntryMMGen(MnemonicEntry):
	wl_id = 'mmgen'
	modname = 'baseconv'
	entry_modes = ('full', 'minimal', 'fixed')
	dfl_entry_mode = 'minimal'
	has_chksum = False

class MnemonicEntryBIP39(MnemonicEntry):
	wl_id = 'bip39'
	modname = 'bip39'
	entry_modes = ('full', 'short', 'fixed')
	dfl_entry_mode = 'fixed'
	has_chksum = True

class MnemonicEntryMonero(MnemonicEntry):
	wl_id = 'xmrseed'
	modname = 'xmrseed'
	entry_modes = ('full', 'short')
	dfl_entry_mode = 'short'
	has_chksum = True

def mn_entry(cfg, wl_id, entry_mode=None):
	if wl_id == 'words':
		wl_id = 'mmgen'
	me = MnemonicEntry.get_cls_by_wordlist(wl_id)(cfg)
	import importlib
	me.bconv = getattr(importlib.import_module(f'mmgen.{me.modname}'), me.modname)(wl_id)
	me.wl = me.bconv.digits
	if entry_mode:
		me.em = getattr(sys.modules[__name__], 'MnEntryMode' + capfirst(entry_mode))(me)
	return me
