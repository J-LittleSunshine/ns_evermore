# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.config import NS_CONFIG_FILE_PATH, NS_ENV, ns_config
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsEvermoreError,
    NsRuntimeError,
    NsStateError,
    NsValidationError,
)
from ns_common.logger import close_ns_loggers, get_ns_logger
from ns_common.paths import DATA_DIR, ETC_DIR, LOG_DIR, ROOT_DIR, SQL_DIR, TMP_DIR

if TYPE_CHECKING:
    pass

__all__ = [
    "__version__",
    "DATA_DIR",
    "ETC_DIR",
    "LOG_DIR",
    "NS_CONFIG_FILE_PATH",
    "NS_ENV",
    "ROOT_DIR",
    "SQL_DIR",
    "TMP_DIR",
    "ns_config",
    "close_ns_loggers",
    "get_ns_logger",
    "NsConfigError",
    "NsDependencyError",
    "NsEvermoreError",
    "NsRuntimeError",
    "NsStateError",
    "NsValidationError",
]

__version__ = "0.0.1"

t = {
    "status_msg": "识别状态描述",
    "status_code": "识别状态码",
    "result": {
        "ocr_result": {
            "msg": "OCR识别状态信息",
            "code": "OCR识别状态码",
            "output": {
                "payee": "收款人",
                "issuer": "开票人",
                "remarks": "备注",
                "password": [
                    # 密码区密码
                ],
                "raw_type": "原始发票类型代码",
                "reviewer": "复核人",
                "total_tax": "合计税额",
                "buyer_name": "购买方名称",
                "total_page": "总页数",
                "detail_info": [
                    # 明细信息
                ],
                "seller_name": "销售方名称",
                "stamp_exits": "是否存在监制章",
                "current_page": "当前页数",
                "invoice_code": "发票代码",
                "invoice_date": "开票日期",
                "invoice_type": "发票类型",
                "total_amount": "合计金额",
                "buyer_address": "购买方地址",
                "sub_total_tax": "小计税额",
                "invoice_amount": "发票金额",
                "invoice_number": "发票号码",
                "seller_address": "销售方地址",
                "buyer_bank_name": "购买方开户行名称",
                "price_tax_amount": "价税合计",
                "seller_bank_name": "销售方开户行名称",
                "sub_total_amount": "小计金额",
                "buyer_taxpayer_id": "购买方纳税人识别号",
                "buyer_bank_account": "购买方银行账号",
                "invoice_check_code": "发票校验码",
                "seller_taxpayer_id": "销售方纳税人识别号",
                "seller_bank_account": "销售方银行账号",
                "invoice_machine_code": "机器码",
                "price_tax_amount_capital": "价税合计大写"
            },
            "det_time": "0.00",
            "rec_time": "0.00",
            "total_time": "0.00"
        },
        "qrcode_result": {
            "msg": "二维码识别状态信息",
            "code": "二维码识别状态码",
            "output": {
                "payee": "收款人",
                "issuer": "开票人",
                "raw_type": "原始发票类型代码",
                "reviewer": "复核人",
                "total_page": "总页数",
                "stamp_exits": "是否存在监制章",
                "current_page": "当前页数",
                "invoice_code": "发票代码",
                "invoice_date": "开票日期",
                "invoice_type": "发票类型",
                "invoice_amount": "发票金额",
                "invoice_number": "发票号码",
                "invoice_check_code": "发票校验码"
            },
            "total_time": "二维码识别耗时"
        },
        "verify_result": {
            "msg": "验真状态信息",
            "code": "验真状态码",
            "output": {
                "base_info": {
                    "amount": "发票金额",
                    "cashier": "",
                    "pdf_url": "PDF下载地址",
                    "remarks": "备注",
                    "buyer_id": "购买方纳税人识别号",
                    "seller_id": "销售方纳税人识别号",
                    "buyer_name": "购买方名称",
                    "check_code": "发票校验码",
                    "net_amount": "发票不含税金额",
                    "tax_amount": "发票价税合计",
                    "seller_name": "销售方名称",
                    "invoice_code": "发票代码",
                    "invoice_date": "开票日期",
                    "invoice_type": "发票类型",
                    "verify_count": "验真次数",
                    "buyer_account": "购买方银行账号",
                    "invoice_number": "发票号码",
                    "invoice_status": "发票状态",
                    "seller_account": "销售方银行账号",
                    "taxation_bureau": "所属税局",
                    "buyer_addr_phone": "购买方地址电话",
                    "seller_addr_phone": "销售方地址电话",
                    "original_invoice_type": "原始发票类型代码",
                },
                "file_name": "",
                "record_id": "",
                "time_used": "验真耗时",
                "detail_info": [
                    {
                        "idx": "明细序号",
                        "unit": "明细单位",
                        "amount": "明细金额",
                        "quantity": "明细数量",
                        "tax_rate": "明细税率",
                        "net_amount": "明细不含税金额",
                        "product_id": "明细商品编码",
                        "tax_amount": "明细税额",
                        "unit_price": "明细单价",
                        "product_name": "明细商品名称",
                        "invoice_number": "发票号码",
                        "invoicing_unit": "明细开票单位",
                        "specifications": "明细规格型号"
                    }
                ],
                "retry_count": "验真重试次数",
            },
            "total_time": "验真耗时",
            # 使用的验真参数
            "used_params": {
                "invoice_code": "发票代码",
                "invoice_date": "开票日期",
                "invoice_type": "原始发票代码",
                "invoice_amount": "发票金额",
                "invoice_number": "发票号码",
                "invoice_check_code": "发票校验码"
            }
        }
    },
    "task_time": "识别耗时",
    "extra_params": {
        "file_url": "影像件地址"
    }
}
