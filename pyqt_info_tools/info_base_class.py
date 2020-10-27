from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QIcon

from copy import copy, deepcopy
import traceback
import sys
import logging
from PyQt5.QtWidgets import QInputDialog
from .waiting_spinner import QtWaitingSpinner, StartRunnable, StopRunnable
from .config import config

import threading


class CustomDropdown(QtWidgets.QWidget):

    def __init__(self, parent=None, *args, **kwargs):

        self.attr = kwargs.get('attr')
        self.instance = kwargs.get('instance', None)

        self.source_instance = kwargs.get('source_instance')
        self.source_attr = kwargs.get('source_attr')

        self._name_source_fcn = kwargs.get('name_source_fcn', None)  # fcn which returns choice_names
        self._value_source_fcn = kwargs.get('value_source', None)  # fcn which returns choice_values

        self.update_fcn = kwargs.get('update_fcn', None)

        self._choice_value_updated_fcn = kwargs.get('choice_value_updated_fcn',
                                                     None)  # fcn which is executed when the attribute of the instance is changed and updates the gui element

        super(CustomDropdown, self).__init__(parent)
        self.button = QtWidgets.QComboBox()
        self.button.instance_attr = deepcopy(self.attr)
        self.button.instance = self.instance
        lay = QtWidgets.QHBoxLayout(self)
        lay.addWidget(self.button, alignment=QtCore.Qt.AlignRight)
        lay.setContentsMargins(0, 0, 0, 0)

        self.choice_list = ChoiceList(gui_element=self.button,
                                      instance=self.instance,
                                      attr=self.attr,
                                      source_instance=self.source_instance,
                                      source_attr=self.source_attr,
                                      name_source_fcn=self._name_source_fcn,
                                      value_source=self._value_source_fcn)
        self.choice_list.update_element()

        self.button.currentIndexChanged.connect(self.update_fcn)
        # if isinstance(self.instance, type):
        #     self.instance.add_cls_observer(self.choice_list.update_element, attr_dependent=[self.attr])
        # else:
        #     self.instance.add_observer(self.choice_list.update_element, attr_dependent=[self.attr])


class ListViewChoice(object):

    def __init__(self, *args, **kwargs):

        self._choice_source_instance = None
        self._list_source_instance = None

        self._instance = kwargs.get('instance', None)

        # list instance's edited attribute
        self.edit_attr = kwargs.get('edit_attr', None)      # attribute of the list instances which are chosen

        # source for list instances
        self._list_source_instance = kwargs.get('list_source_instance', self._instance)
        self._list_source_attr = kwargs.get('list_source_attr', None)
        self._list_name_source_fcn = kwargs.get('list_name_source_fcn', None)  # fcn which returns choice_names
        self._list_value_source_fcn = kwargs.get('list_value_source_fcn', None)  # fcn which returns choice_values

        # choice source
        self._choice_source_instance = kwargs.get('choice_source_instance', self._instance)
        self._choice_source_attr = kwargs.get('choice_source_attr', None)
        self._choice_name_source_fcn = kwargs.get('choice_name_source_fcn', None)  # fcn which returns choice_names
        self._choice_value_source_fcn = kwargs.get('choice_value_source_fcn', None)  # fcn which returns choice_values
        self._choice_value_updated_fcn = kwargs.get('choice_value_updated_fcn', None)  # fcn which is executed when the attribute of the instance is changed and updates the gui element

        self._list_view_widget = kwargs.get('list_view_widget', None)
        self.model = None
        if self._list_view_widget is not None:
            self.model = QtGui.QStandardItemModel(self.list_view_widget)
            self._list_view_widget.setModel(self.model)

        self.list_items_attr = kwargs.get('items_attr')     # attribute of the instance which has the list with the items
        self.list_items = []
        self.item_names = []

        self.update_fcn = kwargs.get('update_fcn', None)

    @property
    def list_source_instance(self):
        return self._list_source_instance

    @list_source_instance.setter
    def list_source_instance(self, value):
        self._list_source_instance = value
        if self._list_source_instance is not None:
            self.observe()

    @property
    def list_source_attr(self):
        return self._list_source_attr

    @list_source_attr.setter
    def list_source_attr(self, value):
        self._list_source_attr = value
        if self._list_source_attr is not None:
            self.observe()
        self.update_element()

    @property
    def choice_source_instance(self):
        return self._choice_source_instance

    @choice_source_instance.setter
    def choice_source_instance(self, value):
        self._choice_source_instance = value
        if self._choice_source_instance is not None:
            self.update_element()

    @property
    def choice_source_attr(self):
        return self._choice_source_attr

    @choice_source_attr.setter
    def choice_source_attr(self, value):
        self._choice_source_attr = value
        if self._choice_source_attr is not None:
            self.update_element()

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, value):
        self._instance = value
        if self.list_source_instance is None:
            self.list_source_instance = self._instance
        if self.choice_source_instance is None:
            self.choice_source_instance = self._instance
        self.update_element()

    @property
    def list_view_widget(self):
        return self._list_view_widget

    @list_view_widget.setter
    def list_view_widget(self, value):
        model = QtGui.QStandardItemModel(self.list_view_widget)
        value.setModel(model)
        self._list_view_widget = value
        self.model = model
        self._list_view_widget.setSpacing(5)

    def update_element(self, *args, **kwargs):
        if self.list_view_widget is None:
            return

        self.generate_items()
        self.generate_item_names()
        self.list_view_widget.blockSignals(True)
        self.model.clear()
        for i, list_item in enumerate(self.list_items):
            item = QtGui.QStandardItem(self.item_names[i])
            item.instance = list_item
            self.model.appendRow(item)
            self.list_view_widget.setIndexWidget(item.index(),
                                                 CustomDropdown(instance=list_item,
                                                                attr=self.edit_attr,
                                                                source_instance=self.choice_source_instance,
                                                                source_attr=self.choice_source_attr,
                                                                name_source_fcn=self._choice_name_source_fcn,
                                                                value_source=self._choice_value_source_fcn,
                                                                update_fcn=self.update_fcn,
                                                                choice_value_updated_fcn=self._choice_value_updated_fcn
                                                                ))

    def generate_items(self):

        if self._list_value_source_fcn is not None:
            self.list_items = self._list_value_source_fcn(self.instance)
        else:
            list_items = getattr(self.list_source_instance, self.list_items_attr)

            if isinstance(list_items, list):
                self.list_items = list_items
            elif isinstance(list_items, dict):
                self.list_items = list(list_items.values())
            else:
                self.list_items = list(list_items)

    def generate_item_names(self):

        if self._list_name_source_fcn is not None:
            self.item_names = self._list_name_source_fcn(self.instance)
        else:
            list_items = getattr(self.list_source_instance, self.list_items_attr)
            self.item_names = ['unnamed'] * self.list_items.__len__()

            if isinstance(list_items, list):
                for i, list_item in enumerate(list_items):
                    if hasattr(list_item, 'name'):
                        self.item_names[i] = list_item.name
                    elif hasattr(list_item, 'id'):
                        self.item_names[i] = str(list_item.id)
                    else:
                        self.item_names[i] = str(list_item)

            elif isinstance(list_items, dict):
                for i, (key, list_item) in enumerate(list_items.items()):
                    if isinstance(list_item, type):
                        if hasattr(list_item, 'visible_class_name'):
                            self.item_names[i] = list_item.visible_class_name
                        else:
                            self.item_names[i] = list_item.__name__
                    else:
                        if hasattr(list_item, 'name'):
                            self.item_names[i] = list_item.name
                        elif hasattr(list_item, 'id'):
                            self.item_names[i] = str(list_item.id)
                        else:
                            self.item_names[i] = str(key)

    def observe(self):
        if (self.list_source_instance is not None) and (self.list_source_attr is not None):
            if isinstance(self.list_source_instance, type):
                self.list_source_instance.add_cls_observer(self.update_element, attr_dependent=[self.list_source_attr])
                logging.debug(
                    f'added observer self.update_element to db_handler, attr_dependent={[self.list_source_attr]}')
            else:
                self.list_source_instance.add_observer(self.update_element, attr_dependent=[self.list_source_attr])
                logging.debug(f'added observer self.update_element to db_handler, attr_dependent={[self.list_source_attr]}')


class ChoiceList(object):
    """
    object which holds and updates the choices. Used for 'choice' type of InfoBaseClass.
    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :key attr: the attribute of the instance
        :key instance: the instance
        :key gui_element: the gui element
        :key source_instance: the instance having the values
        :key source_attr: the attribute of the source instance having the values
        :key name_source_fcn: the function which returns the names of the choices as list
        :key value_source_fcn: the function which returns the values of the choices as list
        :key choice_names: list of the choices names
        :key choice_values: list of the choices values
        """

        self._gui_element = kwargs.get('gui_element', None)

        self.attr = kwargs.get('attr', None)                            # the attribute of the instance
        self._instance = kwargs.get('instance', None)
        self.gui_element = kwargs.get('gui_element', None)

        self._source_instance = kwargs.get('source_instance', self.instance)      # observe this instance
        self._source_attr = kwargs.get('source_attr', None)                       # observe changes of this attribute
        self._name_source_fcn = kwargs.get('name_source_fcn', None)               # fcn which returns choice_names
        self._value_source_fcn = kwargs.get('value_source', None)                 # fcn which returns choice_values

        self.observe()

        self._choice_names = kwargs.get('choice_names', [])
        self._choice_values = kwargs.get('choice_values', [])

        if self._gui_element is not None:
            self._gui_element.choice_names = self.choice_names
            self._gui_element.choice_values = self.choice_values

        self.update_element()

    @property
    def choice_names(self):
        return self._choice_names

    @choice_names.setter
    def choice_names(self, value):
        if value == self._choice_names:
            return
        self._choice_names = value
        self.update_gui_element_choices()

    @property
    def choice_values(self):
        return self._choice_values

    @choice_values.setter
    def choice_values(self, value):
        if value == self._choice_values:
            return
        self._choice_values = value
        self.update_gui_element_choices()

    @property
    def gui_element(self):
        return self._gui_element

    @gui_element.setter
    def gui_element(self, value):
        if value == self._gui_element:
            return
        self._gui_element = value
        self._gui_element.choice_names = self.choice_names
        self._gui_element.choice_values = self.choice_values

        self.update_element()

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, value):
        if value == self._instance:
            return
        self._instance = value
        if self.source_instance is None:
            self.source_instance = self._instance
        self.observe()
        self.update_element()

    @property
    def source_instance(self):
        return self._source_instance

    @source_instance.setter
    def source_instance(self, value):
        if value == self._source_instance:
            return
        if self.source_instance is not None:
            self.source_instance.remove_observer(self.update_element)
        self._source_instance = value
        self.observe()
        self.update_element()

    @property
    def source_attr(self):
        return self._source_attr

    @source_attr.setter
    def source_attr(self, value):
        if value == self._source_attr:
            return
        self._source_attr = value
        self.observe()
        self.update_element()

    @property
    def name_source_fcn(self):
        return self._name_source_fcn

    @name_source_fcn.setter
    def name_source_fcn(self, value):
        if value == self._name_source_fcn:
            return
        self._name_source_fcn = value
        self.observe()

    @property
    def value_source_fcn(self):
        return self._value_source_fcn

    @value_source_fcn.setter
    def value_source_fcn(self, value):
        if value == self._value_source_fcn:
            return
        self._value_source_fcn = value
        self.observe()

    def observe(self):
        if self.source_instance is not None:
            if isinstance(self.source_instance, type):
                self.source_instance.add_cls_observer(self.update_element, attr_dependent=[self.list_source_attr])
                logging.debug(
                    f'added observer self.update_element to db_handler, attr_dependent={[self.list_source_attr]}')
            else:
                self.source_instance.add_observer(self.update_element, attr_dependent=[self.source_attr])
                logging.debug(f'added observer self.update_element to db_handler, attr_dependent={[self.source_attr]}')

        if self.instance is not None:
            if isinstance(self.instance, type):
                self.instance.add_cls_observer(self.update_element, attr_dependent=[self.attr])
            else:
                self.instance.add_observer(self.update_element, attr_dependent=[self.attr])

    def update_gui_element_choices(self):

        if self.choice_values.__len__() != self.choice_names.__len__():
            return

        self.gui_element.blockSignals(True)
        self.gui_element.clear()
        for i, name in enumerate(self.choice_names):
            # item = QListWidgetItem()
            # item.setText(str(name))
            # item.instance = self.choice_values[i]
            if hasattr(self.choice_values[i], 'ClassIcon'):
                icon = QIcon(self.choice_values[i].ClassIcon)
                self.gui_element.addItem(icon, name)
            else:
                self.gui_element.addItem(name)

    def update_element(self, *args, ** kwargs):

        if self.gui_element is None:
            return

        self.update_choices()

        cur_val = getattr(self.instance, self.attr)
        if cur_val is not None:
            if cur_val in list(self.choice_values):
                cur_index = list(self.choice_values).index(cur_val)
                self.gui_element.setCurrentIndex(cur_index)
        self.gui_element.blockSignals(False)

    def update_choices(self):

        if self.name_source_fcn is not None:
            if self.name_source_fcn is self.value_source_fcn:
                if self.source_instance is None:
                    source_instance = self.instance
                else:
                    source_instance = self.source_instance
                self.choice_names, self.choice_values = self.value_source_fcn(source_instance)
            else:
                self.choice_names = self._name_source_fcn()
                self.choice_values = self._value_source_fcn()

        else:
            if self.name_source_fcn is not None:
                choice_names = self.name_source_fcn(self.source_instance)
            else:
                choice_names = getattr(self.source_instance, self.source_attr)
                choice_names_list = []
                if isinstance(choice_names, dict):
                    for key, choice_name in choice_names.items():
                        if isinstance(choice_name, type):
                            if hasattr(choice_name, 'visible_class_name'):
                                choice_names_list.append(choice_name.visible_class_name)
                            else:
                                choice_names_list.append(choice_name.__name__)
                        else:
                            if hasattr(choice_name, 'name'):
                                choice_names_list.append(choice_name.name)
                            else:
                                choice_names_list.append(str(key))
                else:
                    choice_names_list = []
                    for choice_name in choice_names:
                        if isinstance(choice_name, type):
                            if hasattr(choice_name, 'visible_class_name'):
                                choice_names_list.append(choice_name.visible_class_name)
                            else:
                                choice_names_list.append(choice_name.__name__)
                        else:
                            if hasattr(choice_name, 'name'):
                                choice_names_list.append(choice_name.name)
                            elif hasattr(choice_name, 'id'):
                                choice_names_list.append(choice_name.id)
                            else:
                                choice_names_list.append(str(choice_name))
                choice_names = choice_names_list

            if self.value_source_fcn is not None:
                choice_values = self.value_source_fcn(self.source_instance)
            else:
                choice_values = getattr(self.source_instance, self.source_attr)
                if isinstance(choice_values, dict):
                    choice_values = list(choice_values.values())
                elif not isinstance(choice_values, list):
                    choice_values = list(choice_values)
                else:
                    choice_values = choice_values

            self.choice_names = choice_names
            self.choice_values = choice_values



    def generate_from_observed_instance_attr(self, attr, source_instance=None):
        """

        :param source_instance: the observed instance
        :param attr: the observed attribute
        :return:
        """

        if source_instance is None:
            self.source_instance = self.instance
        else:
            self.source_instance = source_instance
        self.source_attr = attr
        fcn = lambda x: get_names_and_values_list(x, self.source_attr)
        self.name_source_fcn = fcn
        self.value_source_fcn = fcn
        self.update_element()


class CustomDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        QtWidgets.QDialog.__init__(self, *args, **kwargs)
        self.spinner = QtWaitingSpinner(self, True, True, QtCore.Qt.ApplicationModal)
        self.__running = False

    def resizeEvent(self, event):
        self.spinner.updateSize()
        event.accept()

    @QtCore.pyqtSlot()
    def finished_process(self):
        print('stop spinner')
        if self.__running:
            self.spinner.stop()
            self.__running = False

    @QtCore.pyqtSlot()
    def start_process(self):
        print('start spinner')
        if not self.__running:
            self.spinner.start()
            self.__running = True

    def start_waiting(self, fcn=None, args=(), kwargs={}):
        # QtCore.QThreadPool.globalInstance().start(StartRunnable(dialog=self))
        start_runnable = StartRunnable(dialog=self, fcn=fcn, args=args, kwargs=kwargs)
        # config.app.threadpool.start(start_runnable)
        QtCore.QThreadPool.globalInstance().start(start_runnable)

    def stop_waiting(self):
        # QtCore.QThreadPool.globalInstance().start(StopRunnable(dialog=self))
        stop_runnable = StopRunnable(dialog=self)
        # config.app.threadpool.start(stop_runnable)
        QtCore.QThreadPool.globalInstance().start(stop_runnable)


def get_names_and_values_list(obj, attr):

    if obj is None:
        return [], []

    x = getattr(obj, attr)

    if x is None:
        return [], []

    names = [''] * x.__len__()
    values = [None] * x.__len__()

    if isinstance(x, dict):
        for i, (key, value) in enumerate(x.items()):
            if hasattr(value, 'name'):
                names[i] = value.name
            else:
                names[i] = str(key)
            values[i] = value
    elif isinstance(x, list) or isinstance(x, set):
        for i, value in enumerate(x):
            if hasattr(value, 'name'):
                names[i] = value.name
            elif hasattr(value, 'id'):
                names[i] = str(value.id)
            else:
                names[i] = str(value)
            values[i] = value

    return names, values


class InfoBaseClass(object):
    """

    ------------------------------------------------------------------------------------------------------------
    Type:                       qt element              element name:
    ------------------------------------------------------------------------------------------------------------
    [int, float, str]:          line edit               {key}_lineEdit
    [bool]:                     radio_button            {key}_radioButton
    ['text']:                   textEdit                {key}_textEdit
    ['static']:                 label                   {key}_label
    ['object']                  label                   {key}_label                 (single element)
    ['object']                  listWidget              {key}_listWidget            (multiple elements)
    ['choice']                  comboBox                {key}_comboBox


    -----------------
    Available types:
    -----------------

    int_type = {'type': int, 'bottom': None, 'top': None, 'direct_edit': True}
    float_type = {'type': float, 'bottom': None, 'top': None, 'direct_edit': True}
    str_type = {'type': str, 'direct_edit': True}
    bool_type = {'type': bool, 'direct_edit': True}
    text_type = {'type': 'text', 'direct_edit': True}
    static_str = {'type': 'static', 'sub_type': str}

    - '<attr_bool>': bool_type

    - '<attr_int>': int_type

    - 'attr_float': float_type

    - '<static_string>': static_str

    - '<single_object>': {'type': 'object',
                          'select': {'type': 'single',
                                     'selectable_objects': [<selectable_obj_gui_cls>]},
                        '  direct_edit': True}

    - '<multiple_objects': {'type': 'object',
                                    'select': {'type': 'multiple',
                                               'selectable_objects': [<selectable_obj_gui_cls1>,
                                               <selectable_obj_gui_cls2>]
                                               }
                            'direct_edit': True},

    - '<attr_choice>' = {'type': 'choice', 'choices': {'choice_name1': choice1,
                                                       'choice_name2': choice2
                                                       }
                         }

    - '<attr_choice>' = {'type': 'choice', 'choices': ChoicesList()}


    edit and new:
    -------------
    For objects

    edit object:
    {key}_edit_pushButton

    add new:
    Create a qt pushButton with the name:   {key}_new_pushButton
    create_new()


    """

    choice_type = {'type': 'choice', 'choices': {}}
    int_type = {'type': int, 'bottom': None, 'top': None, 'direct_edit': True}
    float_type = {'type': float, 'bottom': None, 'top': None, 'direct_edit': True}
    str_type = {'type': str, 'direct_edit': True}
    bool_type = {'type': bool, 'direct_edit': True}
    text_type = {'type': 'text', 'direct_edit': True}
    static_str = {'type': 'static', 'sub_type': str}
    object = {'type': 'object',
              'select': {'type': 'single',
                         'max_num_selection': None,
                         'selectable_objects': None},
              'direct_edit': True}

    editable_attributes = {'name': str_type,
                           'id': static_str,
                           'pid': static_str,
                           }

    def __init__(self, *args, **kwargs):

        ui_info = kwargs.get('ui_info', None)

        self._new_cls = kwargs.get('cls', None)
        self.create_new = kwargs.get('create_new', False)

        self.instance = kwargs.get('instance', None)
        if self.instance is not None:
            if hasattr(self.instance, 'selected'):
                self.instance.selected = True

        self.instance.info = self

        self.main_window = kwargs.get('main_window', None)

        self.key_gui_lookup_dict = {}

        self.values = {}
        for key in self.editable_attributes.keys():
            self.values[key] = getattr(self.instance, key)
        self.initial_values = copy(self.values)

        if self.main_window is None:
            if config.app is not None:
                if hasattr(config.app, 'MainWindow'):
                    self.dialog = CustomDialog(config.app.MainWindow)
                else:
                    self.dialog = CustomDialog()
            else:
                self.dialog = CustomDialog()
        else:
            self.dialog = CustomDialog(self.main_window)

        self.waiting_dialog = self.dialog.spinner

        self.set_style()
        self.dialog.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
        self.dialog.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.dialog.ui = ui_info()
        self.dialog.ui.setupUi(self.dialog)

        self.connect_to_gui_editor()

        self.dialog.closeEvent = self.close_event
        self.info_edit = None

        self.dialog.accepted = False

        self._selection_handler = None

        self.selection_handler = config.app.selection_handler
        self.selection_handler.set_selectable_classes([])
        self.selection_handler.max_num_selection = None
        # self.selection_handler.observe(self.edge_selection_changed, attr_dependent=['selected_instances'])
        print(f'{self.__class__.__name__} info initialized')

        self.update_fields()
        self.add_connections()

        self.dialog.ui.buttonBox.accepted.connect(self.accept_event)
        self.dialog.ui.buttonBox.rejected.connect(self.close_event)

        self._edited_attr = None

        self.keep_when_closed = kwargs.get('keep_when_closed', False)

        # self.waiting_dialog.start()

    @property
    def selection_handler(self):
        if self._selection_handler is None:
            self._selection_handler = config.app.selection_handler
        return self._selection_handler

    @selection_handler.setter
    def selection_handler(self, value):
        if self._selection_handler == value:
            return
        self._selection_handler = value

    def add_validators(self):
        pass

    def connect_to_gui_editor(self):

        for key, value in self.editable_attributes.items():
            # find the gui edit element:
            if isinstance(value, dict):
                attr_type = value['type']
            else:
                attr_type = value

            if attr_type in [int, float, str, bool, 'text', 'static', 'object', 'choice', 'list_choice']:

                gui_edit_element_name = None
                if attr_type in [int, float, str]:
                    gui_edit_element_name = f'{key}_lineEdit'
                elif attr_type in [bool]:
                    gui_edit_element_name = f'{key}_radioButton'
                elif attr_type == 'text':
                    gui_edit_element_name = f'{key}_textEdit'
                elif attr_type == 'static':
                    gui_edit_element_name = f'{key}_label'
                elif attr_type == 'object':
                    if value['select']['type'] == 'single':
                        gui_edit_element_name = f'{key}_label'
                    elif value['select']['type'] == 'multiple':
                        gui_edit_element_name = f'{key}_listWidget'
                elif attr_type == 'choice':
                    gui_edit_element_name = f'{key}_comboBox'
                elif attr_type == 'list_choice':
                    if 'key' in self.editable_attributes[key].keys():
                        this_key = self.editable_attributes[key]['key']
                        gui_edit_element_name = f'{this_key}_listView'
                    else:
                        gui_edit_element_name = f'{key}_listView'

                if gui_edit_element_name is None:
                    print(f'attr_type {attr_type} not supported')
                    logging.error(f'attr_type {attr_type} not supported')
                    continue

                if not hasattr(self.dialog.ui, gui_edit_element_name):
                    print(f'Gui edit element for {key} not found')
                    logging.error(f'Gui edit element for {key} not found')
                    continue

                if attr_type in [int, float, str, bool, 'text', 'static']:
                    gui_edit_element = getattr(self.dialog.ui, gui_edit_element_name)
                    self.key_gui_lookup_dict[key] = gui_edit_element
                    print(gui_edit_element)

                    gui_edit_element.instance_attr = deepcopy(key)
                    gui_edit_element.instance = self.instance

                    validator = None
                    # add validator:
                    if isinstance(value, dict):
                        if value['type'] is int:
                            validator = QIntValidator()
                        elif value['type'] is float:
                            validator = QDoubleValidator()
                    else:
                        if value is int:
                            validator = QIntValidator()
                        elif value is float:
                            validator = QDoubleValidator()

                    if 'bottom' in value.keys():
                        if value['bottom'] is not None:
                            validator.setBottom(value['bottom'])
                    if 'top' in value.keys():
                        if value['top'] is not None:
                            validator.setBottom(value['top'])

                    if validator is not None:
                        gui_edit_element.setValidator(validator)

                    if isinstance(gui_edit_element, QtWidgets.QLineEdit) or isinstance(gui_edit_element,
                                                                                       QtWidgets.QTextEdit):
                        cur_val = getattr(self.instance, key)
                        if cur_val is not None:
                            gui_edit_element.setText(str(cur_val))
                        else:
                            gui_edit_element.setText('')
                        gui_edit_element.textChanged.connect(self.update_instance)
                        self.instance.add_observer(self.update_gui_element, attr_dependent=[key])
                    elif isinstance(gui_edit_element, QtWidgets.QRadioButton):
                        cur_val = getattr(self.instance, key)
                        if cur_val is not None:
                            gui_edit_element.setChecked(cur_val)
                        else:
                            gui_edit_element.setChecked(False)
                        gui_edit_element.toggled.connect(self.update_instance)
                        self.instance.add_observer(self.update_gui_element, attr_dependent=[key])
                    elif isinstance(gui_edit_element, QtWidgets.QLabel):
                        cur_val = getattr(self.instance, key)
                        if cur_val is not None:
                            gui_edit_element.setText(str(cur_val))
                        else:
                            gui_edit_element.setText('')
                        self.instance.add_observer(self.update_gui_element, attr_dependent=[key])

                elif attr_type == 'object':
                    cur_val = getattr(self.instance, key)
                    self.instance.add_observer(self.update_gui_element, attr_dependent=[key])

                    if value['select']['type'] == 'single':

                        gui_edit_element_name = f'{key}_label'
                        gui_edit_element = getattr(self.dialog.ui, gui_edit_element_name)
                        self.key_gui_lookup_dict[key] = gui_edit_element
                        if cur_val is not None:
                            gui_edit_element.setText(str(cur_val.name))
                        else:
                            gui_edit_element.setText(str(''))
                        # add click event to show instance info when clicked:
                        gui_edit_element.instance = cur_val
                        print('to implement')
                        gui_edit_element.clicked.connect(self.object_label_clicked)

                    elif value['select']['type'] == 'multiple':
                        gui_edit_element_name = f'{key}_listWidget'
                        gui_edit_element = getattr(self.dialog.ui, gui_edit_element_name)
                        self.key_gui_lookup_dict[key] = gui_edit_element
                        gui_edit_element.itemDoubleClicked.connect(handle_double_click)
                        gui_edit_element.clear()
                        if cur_val is not None:
                            if isinstance(cur_val, list):
                                for instance in cur_val:
                                    item = QListWidgetItem()
                                    if hasattr(instance, 'name'):
                                        item.setText(instance.name)
                                    else:
                                        item.setText(str(instance))
                                    item.instance = instance
                                    if hasattr(item, 'ClassIcon'):
                                        item.setIcon(QIcon(item.ClassIcon))
                                    gui_edit_element.addItem(item)

                            elif isinstance(cur_val, dict):
                                for key, instance in cur_val.items():
                                    item = QListWidgetItem()
                                    if hasattr(instance, 'name'):
                                        item.setText(instance.name)
                                    else:
                                        item.setText(str(key))
                                    item.instance = instance
                                    if hasattr(item, 'ClassIcon'):
                                        item.setIcon(QIcon(item.ClassIcon))
                                    gui_edit_element.addItem(item)

                    edit_button_gui_edit_element_name = f'{key}_edit_pushButton'
                    if not hasattr(self.dialog.ui, edit_button_gui_edit_element_name):
                        print(f'Gui edit button for {key} not found')
                        logging.error(f'Gui edit button for {key} not found')
                    else:
                        edit_button = getattr(self.dialog.ui, edit_button_gui_edit_element_name)
                        edit_button.instance_attr = deepcopy(key)
                        edit_button.clicked.connect(self.select_objects)

                    add_new_button_name = f'{key}_new_pushButton'
                    if not hasattr(self.dialog.ui, add_new_button_name):
                        print(f'No Gui add new button for {key} found')
                        logging.error(f'No Gui add new button for {key} found')
                    else:
                        add_new_button = getattr(self.dialog.ui, add_new_button_name)
                        add_new_button.instance_attr = deepcopy(key)
                        add_new_button.clicked.connect(self.add_new_object)

                elif attr_type == 'choice':

                    gui_edit_element = getattr(self.dialog.ui, gui_edit_element_name)
                    gui_edit_element.instance_attr = deepcopy(key)
                    gui_edit_element.instance = self.instance

                    self.key_gui_lookup_dict[key] = gui_edit_element
                    print(gui_edit_element)

                    # init_gui_element:
                    # ---------------------------

                    if isinstance(value['choices'], ChoiceList):
                        choice_list = value['choices']
                        choice_list.instance = self.instance
                        choice_list.attr = key
                        choice_list.gui_element = gui_edit_element
                        # choice_list.update_element()
                    else:
                        # add all choices
                        gui_edit_element.addItems(value['choices'].keys())

                    # set current index:
                    cur_val = getattr(self.instance, key)
                    if cur_val is not None:
                        if cur_val in list(value['choices'].choice_values):
                            cur_index = list(value['choices'].choice_values).index(cur_val)
                            gui_edit_element.setCurrentIndex(cur_index)

                    # connect to changes
                    gui_edit_element.currentIndexChanged.connect(self.update_instance)

                elif attr_type == 'list_choice':
                    gui_edit_element = getattr(self.dialog.ui, gui_edit_element_name)
                    gui_edit_element.instance_attr = deepcopy(key)
                    self.key_gui_lookup_dict[key] = gui_edit_element
                    print(gui_edit_element)

                    if isinstance(value['object'], ListViewChoice):
                        choice_list = value['object']
                        choice_list.instance = self.instance
                        choice_list.update_fcn = self.update_instance
                        # if 'key' in self.editable_attributes[key].keys():
                        #     this_key = self.editable_attributes[key]['key']
                        # else:
                        #     this_key = key
                        # choice_list.edit_attr = this_key
                        choice_list.list_view_widget = gui_edit_element
                        choice_list.update_element()
                    else:
                        # add all choices
                        gui_edit_element.addItems(value['choices'].keys())

    def show_attribute_info(self, *args, **kwargs):
        gui_edit_element = self.dialog.sender()
        instance_attr = gui_edit_element.instance_attr
        instance = getattr(self.instance, instance_attr)
        if hasattr(instance, 'double_clicked'):
            instance.double_clicked()

    def update_instance(self, *args, **kwargs):
        gui_edit_element = self.dialog.sender()
        instance_attr = gui_edit_element.instance_attr

        dict_entry = self.editable_attributes[instance_attr]

        edit_direct = True
        if isinstance(dict_entry, dict):
            if 'direct_edit' in dict_entry.keys():
                edit_direct = dict_entry['direct_edit']

        new_value = None
        attr_type = None
        raw_value = None

        try:
            if isinstance(gui_edit_element, QtWidgets.QLineEdit):
                raw_value = gui_edit_element.text()
                if raw_value:
                    if isinstance(dict_entry, dict):
                        attr_type = dict_entry['type']
                    else:
                        attr_type = dict_entry
                    if attr_type is int:
                        new_value = int(raw_value)
                    elif attr_type is float:
                        new_value = float(raw_value)
                    elif attr_type is str:
                        new_value = raw_value
            elif isinstance(gui_edit_element, QtWidgets.QRadioButton):
                attr_type = bool
                raw_value = gui_edit_element.isChecked()
                new_value = raw_value
            elif isinstance(gui_edit_element, QtWidgets.QTextEdit):
                raw_value = gui_edit_element.toPlainText()
                attr_type = str
                new_value = raw_value
            elif isinstance(gui_edit_element, QtWidgets.QComboBox):
                index = gui_edit_element.currentIndex()
                new_value = dict_entry['choices'].choice_values[index]
                # gui_edit_element.choice_names
                # QtWidgets.QComboBox.currentText()

        except Exception as e:
            logging.error(f'could not parse {raw_value} to {attr_type}: {e}')
            print(e)
            print(traceback.format_exc())
            print(sys.exc_info()[2])

        if hasattr(gui_edit_element, 'instance'):
            if not (getattr(gui_edit_element.instance, instance_attr) == new_value):
                setattr(gui_edit_element.instance, instance_attr, new_value)
        else:
            if edit_direct:
                if not (getattr(self.instance, instance_attr) == new_value):
                    setattr(self.instance, instance_attr, new_value)

            self.values[instance_attr] = new_value

    def update_gui_element(self, *args, **kwargs):
        key = kwargs.get('attribute', None)
        gui_edit_element = self.key_gui_lookup_dict[key]

        if isinstance(self.editable_attributes[key], dict):
            attr_type = self.editable_attributes[key]['type']
        else:
            attr_type = self.editable_attributes[key]

        if attr_type in [int, float, str, bool, 'text', 'static']:

            if isinstance(gui_edit_element, QtWidgets.QLineEdit) or isinstance(gui_edit_element, QtWidgets.QTextEdit):
                cur_val = getattr(self.instance, key)
                if cur_val is not None:
                    gui_edit_element.setText(str(cur_val))
                else:
                    gui_edit_element.setText('')
            elif isinstance(gui_edit_element, QtWidgets.QRadioButton):
                cur_val = getattr(self.instance, key)
                if cur_val is not None:
                    gui_edit_element.setChecked(cur_val)
                else:
                    gui_edit_element.setChecked(False)
            elif isinstance(gui_edit_element, QtWidgets.QLabel):
                cur_val = getattr(self.instance, key)
                if cur_val is not None:
                    gui_edit_element.setText(str(cur_val))
                else:
                    gui_edit_element.setText('')

        elif attr_type == 'object':
            cur_val = getattr(self.instance, key)
            if self.editable_attributes[key]['select']['type'] == 'single':
                if cur_val is not None:
                    gui_edit_element.setText(str(cur_val.name))
                else:
                    gui_edit_element.setText(str(''))

            elif self.editable_attributes[key]['select']['type'] == 'multiple':
                gui_edit_element.clear()
                if cur_val is not None:
                    for instance in cur_val:
                        item = QListWidgetItem()
                        item.setText(instance.name)
                        item.instance = instance
                        if hasattr(instance, 'ClassIcon'):
                            item.setIcon(QIcon(instance.ClassIcon))
                        gui_edit_element.addItem(item)

    def object_label_clicked(self, *args, **kwargs):
        gui_element = self.dialog.sender()
        if hasattr(gui_element, 'instance'):
            if hasattr(gui_element.instance, 'double_clicked'):
                gui_element.instance.double_clicked()

    def add_new_object(self):
        logging.info(f'Add new...')
        gui_element = self.dialog.sender()
        if not hasattr(gui_element, 'instance_attr'):
            return
        instance_attr = gui_element.instance_attr
        dict_entry = self.editable_attributes[instance_attr]

        if dict_entry['select']['selectable_objects'].__len__() == 1:
            selectable_type = dict_entry['select']['selectable_objects'][0]
        elif dict_entry['select']['selectable_objects'].__len__() > 1:
            selectable_type = getChoice(items=dict_entry['select']['selectable_objects'])
        else:
            selectable_type = None

        if not selectable_type and (selectable_type is None):
            logging.info(f'Can not create new object for type: {selectable_type}')
            print(f'Can not create new object for type: {selectable_type}')
            return

        if not hasattr(selectable_type, 'create_new'):
            logging.info(f'{selectable_type} has no create new method')
            return

        self.dialog.hide()
        new_instance = None
        try:
            new_instance = selectable_type.create_new()
        except Exception as e:
            logging.error(f'Error creating new instance: {e}')
            print(e)
            print(traceback.format_exc())
            print(sys.exc_info()[2])

        self.dialog.show()

        if new_instance is None:
            return
        else:
            if dict_entry['select']['type'] == 'single':
                setattr(self.instance, instance_attr, new_instance)
                self.values[instance_attr] = new_instance
            elif dict_entry['select']['type'] == 'multiple':
                if 'max_num_selection' in dict_entry['select'].keys():
                    max_num_selection = dict_entry['select']['max_num_selection']
                else:
                    max_num_selection = 999999

                if getattr(self.instance, instance_attr) is None:
                    setattr(self.instance, instance_attr, [new_instance])
                    self.values[instance_attr] = [new_instance]
                elif getattr(self.instance, instance_attr).__len__() > max_num_selection:
                    return
                else:
                    instances = deepcopy(getattr(self.instance, instance_attr))
                    instances.append(new_instance)
                    setattr(self.instance, instance_attr, instances)
                    self.values[instance_attr] = instances

    def select_objects(self):
        logging.info(f'Edit object...')

        gui_edit_element = self.dialog.sender()
        if not hasattr(gui_edit_element, 'instance_attr'):
            return
        instance_attr = gui_edit_element.instance_attr
        self._edited_attr = instance_attr

        dict_entry = self.editable_attributes[instance_attr]

        selectable_classes = dict_entry['select']['selectable_objects']
        if not isinstance(selectable_classes, list):
            selectable_classes = [selectable_classes]

        max_num_selection = 9999999
        if dict_entry['select']['type'] == 'single':
            max_num_selection = 1
        elif dict_entry['select']['type'] == 'multiple':
            if 'max_num_selection' in dict_entry['select'].keys():
                max_num_selection = dict_entry['select']['max_num_selection']
            else:
                max_num_selection = 999999

        selected_instances = getattr(self.instance, instance_attr)

        if (not isinstance(selected_instances, list)) and (selected_instances is not None):
            selected_instances = [selected_instances]

        self.dialog.hide()
        self.selection_handler.dialog_selection(dialog_accept_cb=self.object_selected,
                                                dialog_reject_cb=self.object_rejected,
                                                selectable_classes=selectable_classes,
                                                max_num_selection=max_num_selection,
                                                selected_instances=selected_instances)

    def object_selected(self, instance):
        self.dialog.show()
        print(instance)
        inst_str = ', '.join([x.name for x in instance])
        logging.info(f'selected objects: {inst_str}')
        if self._edited_attr is not None:
            if instance is not None:
                setattr(self.instance, self._edited_attr, instance)
                self.values[self._edited_attr] = instance
            else:
                setattr(self.instance, self._edited_attr, None)
                self.values[self._edited_attr] = None
        self._edited_attr = None

    def object_rejected(self):
        key = self._edited_attr
        self._edited_attr = None
        self.dialog.show()
        logging.info(f'{key} selection rejected')

    def add_connections(self):
        pass

    def update_fields(self):
        pass

    def set_style(self, style_string=None):
        if style_string is None:
            # style_string = qdarkstyle.load_stylesheet_pyqt5()
            # style_string = style_string.replace('min-width: 80px;', 'min-width: 10px;')
            style_string = config.app.style
        self.dialog.setStyleSheet(style_string)

    def show_edit_dialog(self):

        self.dialog.show()
        self.dialog.exec_()
        return self.dialog.accepted, self.instance

    def close_event(self, *args, **kwargs):

        # self.selection_handler.remove_observer(self.edge_selection_changed)
        if hasattr(self, 'selection_handler'):
            self.selection_handler.set_selectable_classes([])
            self.selection_handler.max_num_selection = None
        print("X is clicked")
        if self.instance is not None:
            if hasattr(self.instance, 'selected'):
                self.instance.selected = False

        if not self.keep_when_closed:
            self.instance.info = None
            self.dialog.close()
        else:
            self.dialog.hide()

    def accept_event(self):
        for key, value in self.editable_attributes.items():
            try:
                setattr(self.instance, key, self.values[key])
            except Exception as e:
                logging.error(f'{self.instance.name}: Error setattr {key}: {e}')
                print(e)
                print(traceback.format_exc())
                print(sys.exc_info()[2])

        self.dialog.accepted = True
        self.dialog.close()
        logging.debug(f'face info closed with accepted')

        if self.create_new:
            new_instance = None
            try:
                logging.info(f'creating new face {self.instance.name}')
                new_instance = self._new_cls(**self.instance.__dict__)
                logging.info(f'Successfully created new instance: {new_instance.name}')
            except Exception as e:
                logging.error(f'Error creating new instance {self.instance.name}: {e}')
                print(e)
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            self.instance = new_instance

    def start_waiting_dialog(self):
        self.waiting_dialog.start()

    def stop_waiting_dialog(self):
        self.waiting_dialog.stop()

    def __del__(self):
        try:
            self.instance.remove_observer(self.update_gui_element)
        except Exception as e:
            logging.error(f'{self.instance.name}: Error removing observer: {e}')
            print(e)
            print(traceback.format_exc())
            print(sys.exc_info()[2])
        print('all observers removed')


class ObjectLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self, *args, **kwargs)
        self._no_of_clicks = 0
        self.instance = None

    def mousePressEvent(self, event):
        self._no_of_clicks = self._no_of_clicks + 1
        timer = threading.Timer(0.3, self.reset_clicks)
        if self._no_of_clicks > 1:
            double_clicked = True
        else:
            double_clicked = False
        timer.start()
        if double_clicked:
            self.clicked.emit()
        QtWidgets.QLabel.mousePressEvent(self, event)

    def reset_clicks(self):
        self._no_of_clicks = 0


def label_clicked(self, *args, **kwargs):
    if hasattr(self, 'instance'):
        if hasattr(self.instance, 'double_clicked'):
            self.instance.double_clicked()


def handle_double_click(item):
    if hasattr(item, 'instance'):
        if hasattr(item.instance, 'double_clicked'):
            item.instance.double_clicked()


def getChoice(items):
    items_text = []
    for item in items:
        if hasattr(item, 'visible_name'):
            items_text.append(item.visible_name)
        else:
            items_text.append(item.__name__)
    item, okPressed = QInputDialog.getItem(config.app.MainWindow, "Get item", "Names:", items_text, 0, False)
    if okPressed and item:
        print(item)

    return items_text.index(item)

