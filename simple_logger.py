# simple_logger.py - AI-Optimized Diagnostic Logging System
# Designed exclusively for AI analysis and troubleshooting
# Maintains 100% API compatibility with existing codebase

"""
simple_logger.py - AI Diagnostic Logging System
Records detailed execution context for AI-powered troubleshooting
All logs are structured JSON for machine parsing
"""

import os
import json
import platform
import psutil
import sys
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess
import importlib.metadata

class SimpleLogger:
    """AI-optimized diagnostic logger with structured JSON output"""
    
    # Log categories for AI classification
    CATEGORIES = {
        "SYSTEM_INIT": "System initialization and setup",
        "FILE_PROCESSING": "File processing workflow",
        "FONT_ANALYSIS": "Font analysis and embedding checks",
        "EXTERNAL_TOOL": "External tool execution (pdffonts, ghostscript)",
        "OVERPRINT_CHECK": "Overprint and ink coverage analysis",
        "IMAGE_ANALYSIS": "Image compression and resolution checks",
        "REPORT_GENERATION": "Report generation process",
        "GUI_EVENT": "GUI user interactions",
        "ERROR_HANDLING": "Exception and error handling",
        "PERFORMANCE": "Performance metrics and resource usage",
        "VALIDATION": "Data validation and checks",
        "CLEANUP": "Resource cleanup and finalization"
    }
    
    def __init__(self):
        """Initialize AI-optimized logger"""
        # Session identifiers
        self.session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.process_id = os.getpid()
        self.start_time = datetime.now(timezone.utc)
        
        # Log storage
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # JSON Lines log file for AI parsing
        self.log_file = self.log_dir / f"ai_diagnostic_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Active request tracking
        self.active_requests = {}
        self.request_counter = 0
        
        # System environment capture
        self.environment = self._capture_environment()
        
        # Performance tracking
        self.performance_metrics = {
            "cpu_percent": [],
            "memory_usage_mb": [],
            "active_threads": []
        }
        
        # Initialize with system info
        self._log_entry({
            "event_type": "SESSION_START",
            "category": "SYSTEM_INIT",
            "session_info": {
                "session_id": self.session_id,
                "process_id": self.process_id,
                "start_time": self.start_time.isoformat(),
                "environment": self.environment
            }
        })
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture detailed system environment for diagnostics"""
        env = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "python_implementation": platform.python_implementation()
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            },
            "python_packages": self._get_installed_packages(),
            "external_tools": self._detect_external_tools()
        }
        return env
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """Get versions of key packages"""
        packages = {}
        key_packages = [
            'customtkinter', 'Pillow', 'openpyxl', 'reportlab',
            'PyMuPDF', 'pikepdf', 'pdf2image', 'psutil'
        ]
        
        for pkg in key_packages:
            try:
                packages[pkg] = importlib.metadata.version(pkg)
            except:
                packages[pkg] = "not_installed"
        
        return packages
    
    def _detect_external_tools(self) -> Dict[str, Any]:
        """Detect external tool availability and versions"""
        tools = {}
        
        # Check pdffonts (poppler-utils)
        try:
            result = subprocess.run(['pdffonts', '-v'], 
                                  capture_output=True, text=True, timeout=5)
            tools['pdffonts'] = {
                "available": result.returncode == 0,
                "version": result.stderr.strip() if result.stderr else "unknown",
                "path": subprocess.run(['which', 'pdffonts'], 
                                     capture_output=True, text=True).stdout.strip()
            }
        except:
            tools['pdffonts'] = {"available": False, "version": None, "path": None}
        
        # Check Ghostscript
        gs_commands = ['gs', 'gswin64c', 'gswin32c']
        for cmd in gs_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools['ghostscript'] = {
                        "available": True,
                        "command": cmd,
                        "version": result.stdout.strip(),
                        "path": subprocess.run(['which', cmd], 
                                             capture_output=True, text=True).stdout.strip()
                    }
                    break
            except:
                continue
        else:
            tools['ghostscript'] = {"available": False, "version": None, "path": None}
        
        return tools
    
    def _log_entry(self, data: Dict[str, Any]):
        """Write structured log entry for AI parsing"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "thread_id": threading.current_thread().name,
            "thread_ident": threading.current_thread().ident,
            **data
        }
        
        # Add performance metrics periodically
        if hasattr(self, '_should_log_performance') and self._should_log_performance():
            entry["performance_snapshot"] = self._capture_performance()
        
        # Write to JSON Lines file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            # Fallback to stderr if logging fails
            print(json.dumps({
                "emergency_log": True,
                "original_entry": entry,
                "logging_error": str(e)
            }), file=sys.stderr)
    
    def _should_log_performance(self) -> bool:
        """Determine if performance metrics should be logged"""
        # Log performance every 100 entries or on errors
        return hasattr(self, '_log_count') and self._log_count % 100 == 0
    
    def _capture_performance(self) -> Dict[str, Any]:
        """Capture current performance metrics"""
        try:
            process = psutil.Process()
            return {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_info_mb": {
                    "rss": round(process.memory_info().rss / (1024**2), 2),
                    "vms": round(process.memory_info().vms / (1024**2), 2)
                },
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "system_cpu_percent": psutil.cpu_percent(interval=0.1),
                "system_memory_percent": psutil.virtual_memory().percent
            }
        except:
            return {"error": "performance_metrics_unavailable"}
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking related operations"""
        self.request_counter += 1
        return f"req_{self.request_counter}_{uuid.uuid4().hex[:8]}"
    
    # Public API - Maintained for compatibility
    
    def log(self, message, file_path=None):
        """General log (same as info) - for GUI compatibility"""
        self.info(message, file_path)
    
    def info(self, message, file_path=None):
        """Information log"""
        self._log_entry({
            "level": "INFO",
            "category": self._infer_category(message),
            "message": message,
            "file_path": str(file_path) if file_path else None,
            "context": self._extract_context(message, file_path)
        })
    
    def warning(self, message, file_path=None):
        """Warning log"""
        self._log_entry({
            "level": "WARNING",
            "category": self._infer_category(message),
            "message": message,
            "file_path": str(file_path) if file_path else None,
            "context": self._extract_context(message, file_path),
            "diagnostic_hints": self._generate_diagnostic_hints(message, "WARNING")
        })
    
    def error(self, message, file_path=None, exception=None):
        """Error log with full diagnostic information"""
        error_data = {
            "level": "ERROR",
            "category": "ERROR_HANDLING",
            "message": message,
            "file_path": str(file_path) if file_path else None,
            "context": self._extract_context(message, file_path)
        }
        
        if exception:
            error_data["exception"] = {
                "type": type(exception).__name__,
                "module": type(exception).__module__,
                "message": str(exception),
                "args": exception.args if hasattr(exception, 'args') else [],
                "traceback": traceback.format_exc(),
                "stack_frames": self._extract_stack_frames(),
                "locals_at_error": self._safe_extract_locals()
            }
            
            # Add specific handling for common PDF processing errors
            error_data["diagnostic_hints"] = self._generate_diagnostic_hints(
                message, "ERROR", exception
            )
        
        # Capture system state at error time
        error_data["system_state"] = {
            "memory_available_mb": round(psutil.virtual_memory().available / (1024**2), 2),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
        
        self._log_entry(error_data)
    
    def success(self, message, file_path=None):
        """Success log"""
        self._log_entry({
            "level": "SUCCESS",
            "category": self._infer_category(message),
            "message": message,
            "file_path": str(file_path) if file_path else None,
            "context": self._extract_context(message, file_path)
        })
    
    def debug(self, message, file_path=None):
        """Debug log with detailed context"""
        self._log_entry({
            "level": "DEBUG",
            "category": self._infer_category(message),
            "message": message,
            "file_path": str(file_path) if file_path else None,
            "context": self._extract_context(message, file_path),
            "caller_info": self._get_caller_info()
        })
    
    def start_file(self, file_path, file_size=None):
        """File processing start with request tracking"""
        request_id = self._generate_request_id()
        file_path_str = str(file_path)
        
        self.active_requests[file_path_str] = {
            "request_id": request_id,
            "start_time": datetime.now(timezone.utc),
            "file_size": file_size
        }
        
        self._log_entry({
            "level": "INFO",
            "category": "FILE_PROCESSING",
            "event_type": "FILE_START",
            "request_id": request_id,
            "file_path": file_path_str,
            "file_info": {
                "name": Path(file_path).name,
                "size_bytes": file_size,
                "size_readable": self._format_size(file_size) if file_size else None,
                "extension": Path(file_path).suffix,
                "exists": Path(file_path).exists(),
                "is_file": Path(file_path).is_file() if Path(file_path).exists() else None
            }
        })
    
    def end_file(self, file_path, success=True, processing_time=None):
        """File processing end with performance metrics"""
        file_path_str = str(file_path)
        request_info = self.active_requests.get(file_path_str, {})
        request_id = request_info.get("request_id", "unknown")
        
        if processing_time is None and "start_time" in request_info:
            processing_time = (datetime.now(timezone.utc) - request_info["start_time"]).total_seconds()
        
        self._log_entry({
            "level": "SUCCESS" if success else "ERROR",
            "category": "FILE_PROCESSING",
            "event_type": "FILE_END",
            "request_id": request_id,
            "file_path": file_path_str,
            "processing_result": {
                "success": success,
                "processing_time_seconds": processing_time,
                "file_size_bytes": request_info.get("file_size")
            },
            "performance_metrics": self._capture_performance() if not success else None
        })
        
        # Clean up request tracking
        if file_path_str in self.active_requests:
            del self.active_requests[file_path_str]
    
    def log_step(self, step_name, details=None):
        """Processing step with structured details"""
        self._log_entry({
            "level": "DEBUG",
            "category": self._infer_step_category(step_name),
            "event_type": "PROCESSING_STEP",
            "step_name": step_name,
            "details": details,
            "active_requests": list(self.active_requests.keys())
        })
    
    # AI-specific diagnostic methods
    
    def log_external_tool_execution(self, tool_name: str, command: List[str], 
                                   result: subprocess.CompletedProcess, 
                                   execution_time: float):
        """Log external tool execution for diagnostics"""
        self._log_entry({
            "level": "INFO",
            "category": "EXTERNAL_TOOL",
            "event_type": "TOOL_EXECUTION",
            "tool": {
                "name": tool_name,
                "command": command,
                "command_string": ' '.join(command),
                "exit_code": result.returncode,
                "execution_time_ms": round(execution_time * 1000, 2),
                "success": result.returncode == 0
            },
            "output": {
                "stdout_lines": result.stdout.splitlines() if result.stdout else [],
                "stderr_lines": result.stderr.splitlines() if result.stderr else [],
                "stdout_size": len(result.stdout) if result.stdout else 0,
                "stderr_size": len(result.stderr) if result.stderr else 0
            }
        })
    
    def log_validation_result(self, check_type: str, passed: bool, 
                            details: Dict[str, Any], file_path: Optional[str] = None):
        """Log validation check results"""
        self._log_entry({
            "level": "INFO" if passed else "WARNING",
            "category": "VALIDATION",
            "event_type": "VALIDATION_CHECK",
            "validation": {
                "check_type": check_type,
                "passed": passed,
                "details": details,
                "file_path": str(file_path) if file_path else None
            }
        })
    
    # Helper methods for AI diagnostics
    
    def _infer_category(self, message: str) -> str:
        """Infer log category from message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['font', '폰트', 'embed']):
            return "FONT_ANALYSIS"
        elif any(word in message_lower for word in ['image', '이미지', 'resolution']):
            return "IMAGE_ANALYSIS"
        elif any(word in message_lower for word in ['overprint', '오버프린트', 'ink']):
            return "OVERPRINT_CHECK"
        elif any(word in message_lower for word in ['report', '보고서', 'html']):
            return "REPORT_GENERATION"
        elif any(word in message_lower for word in ['gui', 'button', 'click', 'theme']):
            return "GUI_EVENT"
        elif any(word in message_lower for word in ['error', '오류', 'fail', '실패']):
            return "ERROR_HANDLING"
        elif any(word in message_lower for word in ['start', '시작', 'init']):
            return "SYSTEM_INIT"
        elif any(word in message_lower for word in ['process', '처리', 'file', '파일']):
            return "FILE_PROCESSING"
        else:
            return "FILE_PROCESSING"
    
    def _infer_step_category(self, step_name: str) -> str:
        """Infer category from processing step name"""
        step_lower = step_name.lower()
        
        category_keywords = {
            "FONT_ANALYSIS": ['font', 'embed', '폰트'],
            "IMAGE_ANALYSIS": ['image', 'compress', 'resolution', '이미지'],
            "OVERPRINT_CHECK": ['overprint', 'ink', '오버프린트', '잉크'],
            "EXTERNAL_TOOL": ['pdffonts', 'ghostscript', 'gs', 'external']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in step_lower for keyword in keywords):
                return category
        
        return "FILE_PROCESSING"
    
    def _extract_context(self, message: str, file_path: Optional[str]) -> Dict[str, Any]:
        """Extract contextual information from message"""
        context = {}
        
        # Extract numerical values
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', message)
        if numbers:
            context["extracted_numbers"] = numbers
        
        # Extract file information if path provided
        if file_path:
            path_obj = Path(file_path)
            context["file"] = {
                "name": path_obj.name,
                "directory": str(path_obj.parent),
                "extension": path_obj.suffix,
                "size_bytes": path_obj.stat().st_size if path_obj.exists() else None
            }
        
        # Check for specific keywords indicating issues
        issue_keywords = ['fail', 'error', 'missing', 'not found', '실패', '오류', '없음']
        context["potential_issue"] = any(keyword in message.lower() for keyword in issue_keywords)
        
        return context
    
    def _generate_diagnostic_hints(self, message: str, level: str, 
                                  exception: Optional[Exception] = None) -> Dict[str, Any]:
        """Generate AI diagnostic hints based on error patterns"""
        hints = {
            "level": level,
            "message_keywords": self._extract_keywords(message)
        }
        
        if exception:
            exception_type = type(exception).__name__
            
            # Common PDF processing error patterns
            if exception_type == "FileNotFoundError":
                hints["likely_cause"] = "file_not_found"
                hints["check_points"] = ["file_exists", "path_correct", "permissions"]
            elif exception_type == "PermissionError":
                hints["likely_cause"] = "permission_denied"
                hints["check_points"] = ["file_in_use", "folder_permissions", "antivirus"]
            elif "PdfError" in exception_type:
                hints["likely_cause"] = "pdf_corruption_or_encryption"
                hints["check_points"] = ["pdf_valid", "pdf_encrypted", "pdf_version"]
            elif exception_type == "MemoryError":
                hints["likely_cause"] = "insufficient_memory"
                hints["check_points"] = ["file_size", "available_memory", "other_processes"]
            
            # Check for external tool errors
            if "pdffonts" in str(exception).lower():
                hints["external_tool_issue"] = "pdffonts"
                hints["check_installation"] = True
            elif "ghostscript" in str(exception).lower() or "gs" in str(exception).lower():
                hints["external_tool_issue"] = "ghostscript"
                hints["check_installation"] = True
        
        # Pattern matching for common issues
        if "not checked" in message.lower() or "_not_checked" in message:
            hints["validation_skipped"] = True
            hints["likely_reason"] = "external_tool_unavailable"
        
        return hints
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract meaningful keywords for AI analysis"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'is', 'at', 'of', 'on', 'and', 'a', 'to', 'in', 'for', 'with'}
        words = message.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]  # Limit to 10 most relevant
    
    def _extract_stack_frames(self) -> List[Dict[str, Any]]:
        """Extract stack frames for error diagnostics"""
        frames = []
        for frame in traceback.extract_stack()[:-2]:  # Exclude logger frames
            frames.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line
            })
        return frames[-10:]  # Last 10 frames
    
    def _safe_extract_locals(self) -> Dict[str, str]:
        """Safely extract local variables for diagnostics"""
        frame = sys._getframe(2)  # Go up 2 frames
        locals_dict = {}
        
        for key, value in frame.f_locals.items():
            if key.startswith('_'):  # Skip private variables
                continue
            try:
                # Only include simple types
                if isinstance(value, (str, int, float, bool, type(None))):
                    locals_dict[key] = str(value)
                elif isinstance(value, (list, tuple, dict)) and len(str(value)) < 200:
                    locals_dict[key] = str(value)
            except:
                locals_dict[key] = "<unable_to_serialize>"
        
        return locals_dict
    
    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling function"""
        frame = sys._getframe(2)
        return {
            "file": frame.f_code.co_filename,
            "function": frame.f_code.co_name,
            "line": frame.f_lineno
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size (kept for compatibility)"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    # Session management methods
    
    def create_summary(self) -> str:
        """Create session summary (compatibility method)"""
        summary_data = {
            "session_id": self.session_id,
            "duration_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "performance_summary": self._capture_performance()
        }
        
        # Log summary as structured data
        self._log_entry({
            "event_type": "SESSION_SUMMARY",
            "category": "SYSTEM_INIT",
            "summary": summary_data
        })
        
        # Return formatted string for compatibility
        return json.dumps(summary_data, indent=2)
    
    def save_session_stats(self):
        """Save session statistics"""
        stats_file = self.log_dir / f"ai_session_{self.session_id}.json"
        
        session_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "environment": self.environment,
            "active_requests": self.active_requests,
            "log_file": str(self.log_file)
        }
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            self._log_entry({
                "event_type": "SESSION_STATS_SAVED",
                "category": "CLEANUP",
                "stats_file": str(stats_file)
            })
        except Exception as e:
            self.error("Failed to save session stats", exception=e)
    
    def cleanup_old_logs(self, days_to_keep=30):
        """Clean up old log files"""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        cleaned_files = []
        
        try:
            for log_file in self.log_dir.glob("*.jsonl"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
            
            if cleaned_files:
                self._log_entry({
                    "event_type": "LOG_CLEANUP",
                    "category": "CLEANUP",
                    "cleaned_files": cleaned_files,
                    "count": len(cleaned_files)
                })
        except Exception as e:
            self.error("Log cleanup failed", exception=e)
    
    def get_recent_errors(self, count=10):
        """Get recent errors (compatibility method)"""
        # Read last N error entries from log file
        errors = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get('level') == 'ERROR':
                        errors.append(entry)
            return errors[-count:]
        except:
            return []
    
    def get_log_file(self):
        """Get current log file path"""
        return self.log_file
    
    def close(self):
        """Close logger and finalize session"""
        self._log_entry({
            "event_type": "SESSION_END",
            "category": "CLEANUP",
            "session_duration_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "final_performance": self._capture_performance()
        })
        
        self.save_session_stats()
        self.cleanup_old_logs()

# User-friendly error handler (maintained for compatibility)
class UserFriendlyErrorHandler:
    """Compatibility wrapper for error handling"""
    
    ERROR_MESSAGES = {
        'FileNotFoundError': {
            'message': 'PDF file not found',
            'solution': 'Check if file was moved or deleted',
            'log_level': 'ERROR'
        },
        'PermissionError': {
            'message': 'Cannot access file',
            'solution': 'Check if file is in use or permissions',
            'log_level': 'ERROR'
        },
        'pikepdf._qpdf.PdfError': {
            'message': 'Cannot open PDF file',
            'solution': 'File may be corrupted or encrypted',
            'log_level': 'ERROR'
        },
        'MemoryError': {
            'message': 'Insufficient memory',
            'solution': 'Close other programs or use smaller file',
            'log_level': 'ERROR'
        }
    }
    
    @classmethod
    def handle_error(cls, error, logger, file_path=None):
        """Handle error with user-friendly message"""
        error_type = type(error).__name__
        error_info = cls.ERROR_MESSAGES.get(error_type, {
            'message': 'Unexpected error occurred',
            'solution': 'Restart program or contact support',
            'log_level': 'ERROR'
        })
        
        # Log structured error for AI
        logger.error(
            f"{error_info['message']} - {error_info['solution']}", 
            file_path, 
            error
        )
        
        # Return compatibility string
        return f"{error_info['message']}\n{error_info['solution']}"

# Global logger instance (singleton pattern)
_logger_instance = None

def get_logger():
    """Get logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SimpleLogger()
    return _logger_instance

# Test code (only runs when executed directly)
if __name__ == "__main__":
    # Create logger
    logger = get_logger()
    
    # File processing simulation
    test_file = "sample.pdf"
    
    try:
        logger.start_file(test_file, 1024*1024*50)  # 50MB
        
        logger.log_step("Basic information analysis")
        logger.log_step("Page analysis", "48 pages")
        logger.log_step("Font inspection", "12 fonts found")
        
        logger.warning("Font 'Arial-Bold' not embedded", test_file)
        
        # Simulate external tool execution
        import time
        start = time.time()
        result = subprocess.CompletedProcess(
            args=['pdffonts', test_file],
            returncode=0,
            stdout="name                                 type              encoding         emb sub uni object ID\n",
            stderr=""
        )
        logger.log_external_tool_execution("pdffonts", ['pdffonts', test_file], 
                                         result, time.time() - start)
        
        logger.log_step("Ink coverage calculation", "Average 245%")
        
        # Test validation logging
        logger.log_validation_result("font_embedding", False, {
            "total_fonts": 12,
            "embedded_fonts": 10,
            "missing_fonts": ["Arial-Bold", "Times-Roman"]
        }, test_file)
        
        logger.end_file(test_file, success=True, processing_time=45.3)
        
    except Exception as e:
        # User-friendly error handling
        UserFriendlyErrorHandler.handle_error(e, logger, test_file)
        logger.end_file(test_file, success=False)
    
    finally:
        # Close logger
        logger.close()