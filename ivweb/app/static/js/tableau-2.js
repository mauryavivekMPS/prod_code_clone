/*! tableau-2.1.2 */
(function () {
    /*! BEGIN MscorlibSlim */
    var global = {};
    (function (global) {
        "use strict";
        var ss = {__assemblies: {}};
        ss.initAssembly = function assembly(obj, name, res) {
            res = res || {};
            obj.name = name;
            obj.toString = function () {
                return this.name
            };
            obj.__types = {};
            obj.getResourceNames = function () {
                return Object.keys(res)
            };
            obj.getResourceDataBase64 = function (name) {
                return res[name] || null
            };
            obj.getResourceData = function (name) {
                var r = res[name];
                return r ? ss.dec64(r) : null
            };
            ss.__assemblies[name] = obj
        };
        ss.initAssembly(ss, 'mscorlib');
        ss.getAssemblies = function ss$getAssemblies() {
            return Object.keys(ss.__assemblies).map(function (n) {
                return ss.__assemblies[n]
            })
        };
        ss.isNullOrUndefined = function ss$isNullOrUndefined(o) {
            return (o === null) || (o === undefined)
        };
        ss.isValue = function ss$isValue(o) {
            return (o !== null) && (o !== undefined)
        };
        ss.referenceEquals = function ss$referenceEquals(a, b) {
            return ss.isValue(a) ? a === b : !ss.isValue(b)
        };
        ss.mkdict = function ss$mkdict() {
            var a = (arguments.length != 1 ? arguments : arguments[0]);
            var r = {};
            for (var i = 0; i < a.length; i += 2) {
                r[a[i]] = a[i + 1]
            }
            return r
        };
        ss.clone = function ss$clone(t, o) {
            return o ? t.$clone(o) : o
        };
        ss.coalesce = function ss$coalesce(a, b) {
            return ss.isValue(a) ? a : b
        };
        ss.isDate = function ss$isDate(obj) {
            return Object.prototype.toString.call(obj) === '[object Date]'
        };
        ss.isArray = function ss$isArray(obj) {
            return Object.prototype.toString.call(obj) === '[object Array]'
        };
        ss.isTypedArrayType = function ss$isTypedArrayType(type) {
            return ['Float32Array', 'Float64Array', 'Int8Array', 'Int16Array', 'Int32Array', 'Uint8Array', 'Uint16Array', 'Uint32Array', 'Uint8ClampedArray'].indexOf(ss.getTypeFullName(type)) >= 0
        };
        ss.isArrayOrTypedArray = function ss$isArray(obj) {
            return ss.isArray(obj) || ss.isTypedArrayType(ss.getInstanceType(obj))
        };
        ss.getHashCode = function ss$getHashCode(obj) {
            if (!ss.isValue(obj))throw new ss_NullReferenceException('Cannot get hash code of null'); else if (typeof(obj.getHashCode) === 'function')return obj.getHashCode(); else if (typeof(obj) === 'boolean') {
                return obj ? 1 : 0
            } else if (typeof(obj) === 'number') {
                var s = obj.toExponential();
                s = s.substr(0, s.indexOf('e'));
                return parseInt(s.replace('.', ''), 10) & 0xffffffff
            } else if (typeof(obj) === 'string') {
                var res = 0;
                for (var i = 0; i < obj.length; i++)res = (res * 31 + obj.charCodeAt(i)) & 0xffffffff;
                return res
            } else if (ss.isDate(obj)) {
                return obj.valueOf() & 0xffffffff
            } else {
                return ss.defaultHashCode(obj)
            }
        };
        ss.defaultHashCode = function ss$defaultHashCode(obj) {
            return obj.$__hashCode__ || (obj.$__hashCode__ = (Math.random() * 0x100000000) | 0)
        };
        ss.equals = function ss$equals(a, b) {
            if (!ss.isValue(a))throw new ss_NullReferenceException('Object is null'); else if (a !== ss && typeof(a.equals) === 'function')return a.equals(b);
            if (ss.isDate(a) && ss.isDate(b))return a.valueOf() === b.valueOf(); else if (typeof(a) === 'function' && typeof(b) === 'function')return ss.delegateEquals(a, b); else if (ss.isNullOrUndefined(a) && ss.isNullOrUndefined(b))return true; else return a === b
        };
        ss.compare = function ss$compare(a, b) {
            if (!ss.isValue(a))throw new ss_NullReferenceException('Object is null'); else if (typeof(a) === 'number' || typeof(a) === 'string' || typeof(a) === 'boolean')return a < b ? -1 : (a > b ? 1 : 0); else if (ss.isDate(a))return ss.compare(a.valueOf(), b.valueOf()); else return a.compareTo(b)
        };
        ss.equalsT = function ss$equalsT(a, b) {
            if (!ss.isValue(a))throw new ss_NullReferenceException('Object is null'); else if (typeof(a) === 'number' || typeof(a) === 'string' || typeof(a) === 'boolean')return a === b; else if (ss.isDate(a))return a.valueOf() === b.valueOf(); else return a.equalsT(b)
        };
        ss.staticEquals = function ss$staticEquals(a, b) {
            if (!ss.isValue(a))return !ss.isValue(b); else return ss.isValue(b) ? ss.equals(a, b) : false
        };
        ss.shallowCopy = function ss$shallowCopy(source, target) {
            var keys = Object.keys(source);
            for (var i = 0, l = keys.length; i < l; i++) {
                var k = keys[i];
                target[k] = source[k]
            }
        };
        ss.isLower = function ss$isLower(c) {
            var s = String.fromCharCode(c);
            return s === s.toLowerCase() && s !== s.toUpperCase()
        };
        ss.isUpper = function ss$isUpper(c) {
            var s = String.fromCharCode(c);
            return s !== s.toLowerCase() && s === s.toUpperCase()
        };
        if (typeof(window) == 'object') {
            if (!window.Element) {
                window.Element = function () {
                };
                window.Element.isInstanceOfType = function (instance) {
                    return instance && typeof instance.constructor === 'undefined' && typeof instance.tagName === 'string'
                }
            }
            window.Element.__typeName = 'Element'
        }
        ss.clearKeys = function ss$clearKeys(d) {
            for (var n in d) {
                if (d.hasOwnProperty(n)) delete d[n]
            }
        };
        ss.keyExists = function ss$keyExists(d, key) {
            return d[key] !== undefined
        };
        if (!Object.keys) {
            Object.keys = (function () {
                var hasOwnProperty = Object.prototype.hasOwnProperty, hasDontEnumBug = !({toString: null}).propertyIsEnumerable('toString'), dontEnums = ['toString', 'toLocaleString', 'valueOf', 'hasOwnProperty', 'isPrototypeOf', 'propertyIsEnumerable', 'constructor'], dontEnumsLength = dontEnums.length;
                return function (obj) {
                    if (typeof obj !== 'object' && (typeof obj !== 'function' || obj === null)) {
                        throw new TypeError('Object.keys called on non-object')
                    }
                    var result = [], prop, i;
                    for (prop in obj) {
                        if (hasOwnProperty.call(obj, prop)) {
                            result.push(prop)
                        }
                    }
                    if (hasDontEnumBug) {
                        for (i = 0; i < dontEnumsLength; i++) {
                            if (hasOwnProperty.call(obj, dontEnums[i])) {
                                result.push(dontEnums[i])
                            }
                        }
                    }
                    return result
                }
            }())
        }
        ss.getKeyCount = function ss$getKeyCount(d) {
            return Object.keys(d).length
        };
        ss.__genericCache = {};
        ss._makeGenericTypeName = function ss$_makeGenericTypeName(genericType, typeArguments) {
            var result = genericType.__typeName;
            for (var i = 0; i < typeArguments.length; i++)result += (i === 0 ? '[' : ',') + '[' + ss.getTypeQName(typeArguments[i]) + ']';
            result += ']';
            return result
        };
        ss.makeGenericType = function ss$makeGenericType(genericType, typeArguments) {
            var name = ss._makeGenericTypeName(genericType, typeArguments);
            return ss.__genericCache[name] || genericType.apply(null, typeArguments)
        };
        ss.registerGenericClassInstance = function ss$registerGenericClassInstance(instance, genericType, typeArguments, members, baseType, interfaceTypes) {
            var name = ss._makeGenericTypeName(genericType, typeArguments);
            ss.__genericCache[name] = instance;
            instance.__typeName = name;
            instance.__genericTypeDefinition = genericType;
            instance.__typeArguments = typeArguments;
            ss.initClass(instance, genericType.__assembly, members, baseType(), interfaceTypes())
        };
        ss.registerGenericInterfaceInstance = function ss$registerGenericInterfaceInstance(instance, genericType, typeArguments, members, baseInterfaces) {
            var name = ss._makeGenericTypeName(genericType, typeArguments);
            ss.__genericCache[name] = instance;
            instance.__typeName = name;
            instance.__genericTypeDefinition = genericType;
            instance.__typeArguments = typeArguments;
            ss.initInterface(instance, genericType.__assembly, members, baseInterfaces())
        };
        ss.isGenericTypeDefinition = function ss$isGenericTypeDefinition(type) {
            return type.__isGenericTypeDefinition || false
        };
        ss.getGenericTypeDefinition = function ss$getGenericTypeDefinition(type) {
            return type.__genericTypeDefinition || null
        };
        ss.getGenericParameterCount = function ss$getGenericParameterCount(type) {
            return type.__typeArgumentCount || 0
        };
        ss.getGenericArguments = function ss$getGenericArguments(type) {
            return type.__typeArguments || null
        };
        ss.setMetadata = function ss$_setMetadata(type, metadata) {
            if (metadata.members) {
                for (var i = 0; i < metadata.members.length; i++) {
                    var m = metadata.members[i];
                    m.typeDef = type;
                    if (m.adder) m.adder.typeDef = type;
                    if (m.remover) m.remover.typeDef = type;
                    if (m.getter) m.getter.typeDef = type;
                    if (m.setter) m.setter.typeDef = type
                }
            }
            type.__metadata = metadata;
            if (metadata.variance) {
                type.isAssignableFrom = function (source) {
                    var check = function (target, type) {
                        if (type.__genericTypeDefinition === target.__genericTypeDefinition && type.__typeArguments.length == target.__typeArguments.length) {
                            for (var i = 0; i < target.__typeArguments.length; i++) {
                                var v = target.__metadata.variance[i], t = target.__typeArguments[i], s = type.__typeArguments[i];
                                switch (v) {
                                    case 1:
                                        if (!ss.isAssignableFrom(t, s))return false;
                                        break;
                                    case 2:
                                        if (!ss.isAssignableFrom(s, t))return false;
                                        break;
                                    default:
                                        if (s !== t)return false
                                }
                            }
                            return true
                        }
                        return false
                    };
                    if (source.__interface && check(this, source))return true;
                    var ifs = ss.getInterfaces(source);
                    for (var i = 0; i < ifs.length; i++) {
                        if (ifs[i] === this || check(this, ifs[i]))return true
                    }
                    return false
                }
            }
        };
        ss.setMetadata = function ss$_setMetadata(type, metadata) {
        };
        ss.initClass = function ss$initClass(ctor, asm, members, baseType, interfaces) {
            ctor.__class = true;
            ctor.__assembly = asm;
            if (!ctor.__typeArguments) asm.__types[ctor.__typeName] = ctor;
            if (baseType && baseType !== Object) {
                var f = function () {
                };
                f.prototype = baseType.prototype;
                ctor.prototype = new f;
                ctor.prototype.constructor = ctor
            }
            ss.shallowCopy(members, ctor.prototype);
            if (interfaces) ctor.__interfaces = interfaces
        };
        ss.initGenericClass = function ss$initGenericClass(ctor, asm, typeArgumentCount) {
            ctor.__class = true;
            ctor.__assembly = asm;
            asm.__types[ctor.__typeName] = ctor;
            ctor.__typeArgumentCount = typeArgumentCount;
            ctor.__isGenericTypeDefinition = true
        };
        ss.initInterface = function ss$initInterface(ctor, asm, members, baseInterfaces) {
            ctor.__interface = true;
            ctor.__assembly = asm;
            if (!ctor.__typeArguments) asm.__types[ctor.__typeName] = ctor;
            if (baseInterfaces) ctor.__interfaces = baseInterfaces;
            ss.shallowCopy(members, ctor.prototype);
            ctor.isAssignableFrom = function (type) {
                return ss.contains(ss.getInterfaces(type), this)
            }
        };
        ss.initGenericInterface = function ss$initGenericClass(ctor, asm, typeArgumentCount) {
            ctor.__interface = true;
            ctor.__assembly = asm;
            asm.__types[ctor.__typeName] = ctor;
            ctor.__typeArgumentCount = typeArgumentCount;
            ctor.__isGenericTypeDefinition = true
        };
        ss.initEnum = function ss$initEnum(ctor, asm, members, namedValues) {
            ctor.__enum = true;
            ctor.__assembly = asm;
            asm.__types[ctor.__typeName] = ctor;
            ss.shallowCopy(members, ctor.prototype);
            ctor.getDefaultValue = ctor.createInstance = function () {
                return namedValues ? null : 0
            };
            ctor.isInstanceOfType = function (instance) {
                return typeof(instance) == (namedValues ? 'string' : 'number')
            }
        };
        ss.getBaseType = function ss$getBaseType(type) {
            if (type === Object || type.__interface) {
                return null
            } else if (Object.getPrototypeOf) {
                return Object.getPrototypeOf(type.prototype).constructor
            } else {
                var p = type.prototype;
                if (Object.prototype.hasOwnProperty.call(p, 'constructor')) {
                    try {
                        var ownValue = p.constructor;
                        delete p.constructor;
                        return p.constructor
                    } finally {
                        p.constructor = ownValue
                    }
                }
                return p.constructor
            }
        };
        ss.getTypeFullName = function ss$getTypeFullName(type) {
            return type.__typeName || type.name || (type.toString().match(/^\s*function\s*([^\s(]+)/) || [])[1] || 'Object'
        };
        ss.getTypeQName = function ss$getTypeFullName(type) {
            return ss.getTypeFullName(type) + (type.__assembly ? ', ' + type.__assembly.name : '')
        };
        ss.getTypeName = function ss$getTypeName(type) {
            var fullName = ss.getTypeFullName(type);
            var bIndex = fullName.indexOf('[');
            var nsIndex = fullName.lastIndexOf('.', bIndex >= 0 ? bIndex : fullName.length);
            return nsIndex > 0 ? fullName.substr(nsIndex + 1) : fullName
        };
        ss.getTypeNamespace = function ss$getTypeNamespace(type) {
            var fullName = ss.getTypeFullName(type);
            var bIndex = fullName.indexOf('[');
            var nsIndex = fullName.lastIndexOf('.', bIndex >= 0 ? bIndex : fullName.length);
            return nsIndex > 0 ? fullName.substr(0, nsIndex) : ''
        };
        ss.getTypeAssembly = function ss$getTypeAssembly(type) {
            if (ss.contains([Date, Number, Boolean, String, Function, Array], type))return ss; else return type.__assembly || null
        };
        ss._getAssemblyType = function ss$_getAssemblyType(asm, name) {
            var result = [];
            if (asm.__types) {
                return asm.__types[name] || null
            } else {
                var a = name.split('.');
                for (var i = 0; i < a.length; i++) {
                    asm = asm[a[i]];
                    if (!ss.isValue(asm))return null
                }
                if (typeof asm !== 'function')return null;
                return asm
            }
        };
        ss.getAssemblyTypes = function ss$getAssemblyTypes(asm) {
            var result = [];
            if (asm.__types) {
                for (var t in asm.__types) {
                    if (asm.__types.hasOwnProperty(t)) result.push(asm.__types[t])
                }
            } else {
                var traverse = function (s, n) {
                    for (var c in s) {
                        if (s.hasOwnProperty(c)) traverse(s[c], c)
                    }
                    if (typeof(s) === 'function' && ss.isUpper(n.charCodeAt(0))) result.push(s)
                };
                traverse(asm, '')
            }
            return result
        };
        ss.createAssemblyInstance = function ss$createAssemblyInstance(asm, typeName) {
            var t = ss.getType(typeName, asm);
            return t ? ss.createInstance(t) : null
        };
        ss.getInterfaces = function ss$getInterfaces(type) {
            if (type.__interfaces)return type.__interfaces; else if (type === Date || type === Number)return [ss_IEquatable, ss_IComparable, ss_IFormattable]; else if (type === Boolean || type === String)return [ss_IEquatable, ss_IComparable]; else if (type === Array || ss.isTypedArrayType(type))return [ss_IEnumerable, ss_ICollection, ss_IList]; else return []
        };
        ss.isInstanceOfType = function ss$isInstanceOfType(instance, type) {
            if (ss.isNullOrUndefined(instance))return false;
            if (typeof(type.isInstanceOfType) === 'function')return type.isInstanceOfType(instance);
            return ss.isAssignableFrom(type, ss.getInstanceType(instance))
        };
        ss.isAssignableFrom = function ss$isAssignableFrom(target, type) {
            return target === type || (typeof(target.isAssignableFrom) === 'function' && target.isAssignableFrom(type)) || type.prototype instanceof target
        };
        ss.isClass = function Type$isClass(type) {
            return (type.__class == true || type === Array || type === Function || type === RegExp || type === String || type === Error || type === Object)
        };
        ss.isEnum = function Type$isEnum(type) {
            return !!type.__enum
        };
        ss.isFlags = function Type$isFlags(type) {
            return type.__metadata && type.__metadata.enumFlags || false
        };
        ss.isInterface = function Type$isInterface(type) {
            return !!type.__interface
        };
        ss.safeCast = function ss$safeCast(instance, type) {
            if (type === true)return instance; else if (type === false)return null; else return ss.isInstanceOfType(instance, type) ? instance : null
        };
        ss.cast = function ss$cast(instance, type) {
            if (instance === null || typeof(instance) === 'undefined')return instance; else if (type === true || (type !== false && ss.isInstanceOfType(instance, type)))return instance;
            throw new ss_InvalidCastException('Cannot cast object to type ' + ss.getTypeFullName(type))
        };
        ss.getInstanceType = function ss$getInstanceType(instance) {
            if (!ss.isValue(instance))throw new ss_NullReferenceException('Cannot get type of null');
            try {
                return instance.constructor
            } catch (ex) {
                return Object
            }
        };
        ss._getType = function (typeName, asm, re) {
            var outer = !re;
            re = re || /[[,\]]/g;
            var last = re.lastIndex, m = re.exec(typeName), tname, targs = [];
            if (m) {
                tname = typeName.substring(last, m.index);
                switch (m[0]) {
                    case'[':
                        if (typeName[m.index + 1] != '[')return null;
                        for (; ;) {
                            re.exec(typeName);
                            var t = ss._getType(typeName, global, re);
                            if (!t)return null;
                            targs.push(t);
                            m = re.exec(typeName);
                            if (m[0] === ']')break; else if (m[0] !== ',')return null
                        }
                        m = re.exec(typeName);
                        if (m && m[0] === ',') {
                            re.exec(typeName);
                            if (!(asm = ss.__assemblies[(re.lastIndex > 0 ? typeName.substring(m.index + 1, re.lastIndex - 1) : typeName.substring(m.index + 1)).trim()]))return null
                        }
                        break;
                    case']':
                        break;
                    case',':
                        re.exec(typeName);
                        if (!(asm = ss.__assemblies[(re.lastIndex > 0 ? typeName.substring(m.index + 1, re.lastIndex - 1) : typeName.substring(m.index + 1)).trim()]))return null;
                        break
                }
            } else {
                tname = typeName.substring(last)
            }
            if (outer && re.lastIndex)return null;
            var t = ss._getAssemblyType(asm, tname.trim());
            return targs.length ? ss.makeGenericType(t, targs) : t
        };
        ss.getType = function ss$getType(typeName, asm) {
            return typeName ? ss._getType(typeName, asm || global) : null
        };
        ss.getDefaultValue = function ss$getDefaultValue(type) {
            if (typeof(type.getDefaultValue) === 'function')return type.getDefaultValue(); else if (type === Boolean)return false; else if (type === Date)return new Date(0); else if (type === Number)return 0;
            return null
        };
        ss.createInstance = function ss$createInstance(type) {
            if (typeof(type.createInstance) === 'function')return type.createInstance(); else if (type === Boolean)return false; else if (type === Date)return new Date(0); else if (type === Number)return 0; else if (type === String)return ''; else return new type
        };
        var ss_IFormattable = function IFormattable$() {
        };
        ss_IFormattable.__typeName = 'ss.IFormattable';
        ss.IFormattable = ss_IFormattable;
        ss.initInterface(ss_IFormattable, ss, {format: null});
        var ss_IComparable = function IComparable$() {
        };
        ss_IComparable.__typeName = 'ss.IComparable';
        ss.IComparable = ss_IComparable;
        ss.initInterface(ss_IComparable, ss, {compareTo: null});
        var ss_IEquatable = function IEquatable$() {
        };
        ss_IEquatable.__typeName = 'ss.IEquatable';
        ss.IEquatable = ss_IEquatable;
        ss.initInterface(ss_IEquatable, ss, {equalsT: null});
        ss.isNullOrEmptyString = function ss$isNullOrEmptyString(s) {
            return !s || !s.length
        };
        if (!String.prototype.trim) {
            String.prototype.trim = function String$trim() {
                return ss.trimStartString(ss.trimEndString(this))
            }
        }
        ss.trimEndString = function ss$trimEndString(s, chars) {
            return s.replace(chars ? new RegExp('[' + String.fromCharCode.apply(null, chars) + ']+$') : /\s*$/, '')
        };
        ss.trimStartString = function ss$trimStartString(s, chars) {
            return s.replace(chars ? new RegExp('^[' + String.fromCharCode.apply(null, chars) + ']+') : /^\s*/, '')
        };
        ss.trimString = function ss$trimString(s, chars) {
            return ss.trimStartString(ss.trimEndString(s, chars), chars)
        };
        ss.arrayClone = function ss$arrayClone(arr) {
            if (arr.length === 1) {
                return [arr[0]]
            } else {
                return Array.apply(null, arr)
            }
        };
        if (!Array.prototype.map) {
            Array.prototype.map = function Array$map(callback, instance) {
                var length = this.length;
                var mapped = new Array(length);
                for (var i = 0; i < length; i++) {
                    if (i in this) {
                        mapped[i] = callback.call(instance, this[i], i, this)
                    }
                }
                return mapped
            }
        }
        if (!Array.prototype.some) {
            Array.prototype.some = function Array$some(callback, instance) {
                var length = this.length;
                for (var i = 0; i < length; i++) {
                    if (i in this && callback.call(instance, this[i], i, this)) {
                        return true
                    }
                }
                return false
            }
        }
        if (!Array.prototype.forEach) {
            Array.prototype.forEach = function (callback, thisArg) {
                var T, k;
                if (this == null) {
                    throw new TypeError(' this is null or not defined')
                }
                var O = Object(this);
                var len = O.length >>> 0;
                if (typeof callback !== "function") {
                    throw new TypeError(callback + ' is not a function')
                }
                if (arguments.length > 1) {
                    T = thisArg
                }
                k = 0;
                while (k < len) {
                    var kValue;
                    if (k in O) {
                        kValue = O[k];
                        callback.call(T, kValue, k, O)
                    }
                    k++
                }
            }
        }
        if (!Array.prototype.filter) {
            Array.prototype.filter = function (fun) {
                if (this === void 0 || this === null) {
                    throw new TypeError
                }
                var t = Object(this);
                var len = t.length >>> 0;
                if (typeof fun !== 'function') {
                    throw new TypeError
                }
                var res = [];
                var thisArg = arguments.length >= 2 ? arguments[1] : void 0;
                for (var i = 0; i < len; i++) {
                    if (i in t) {
                        var val = t[i];
                        if (fun.call(thisArg, val, i, t)) {
                            res.push(val)
                        }
                    }
                }
                return res
            }
        }
        ss._delegateContains = function ss$_delegateContains(targets, object, method) {
            for (var i = 0; i < targets.length; i += 2) {
                if (targets[i] === object && targets[i + 1] === method) {
                    return true
                }
            }
            return false
        };
        ss._mkdel = function ss$_mkdel(targets) {
            var delegate = function () {
                if (targets.length == 2) {
                    return targets[1].apply(targets[0], arguments)
                } else {
                    var clone = ss.arrayClone(targets);
                    for (var i = 0; i < clone.length; i += 2) {
                        if (ss._delegateContains(targets, clone[i], clone[i + 1])) {
                            clone[i + 1].apply(clone[i], arguments)
                        }
                    }
                    return null
                }
            };
            delegate._targets = targets;
            return delegate
        };
        ss.mkdel = function ss$mkdel(object, method) {
            if (!object) {
                return method
            }
            return ss._mkdel([object, method])
        };
        ss.delegateCombine = function ss$delegateCombine(delegate1, delegate2) {
            if (!delegate1) {
                if (!delegate2._targets) {
                    return ss.mkdel(null, delegate2)
                }
                return delegate2
            }
            if (!delegate2) {
                if (!delegate1._targets) {
                    return ss.mkdel(null, delegate1)
                }
                return delegate1
            }
            var targets1 = delegate1._targets ? delegate1._targets : [null, delegate1];
            var targets2 = delegate2._targets ? delegate2._targets : [null, delegate2];
            return ss._mkdel(targets1.concat(targets2))
        };
        ss.delegateRemove = function ss$delegateRemove(delegate1, delegate2) {
            if (!delegate1 || (delegate1 === delegate2)) {
                return null
            }
            if (!delegate2) {
                return delegate1
            }
            var targets = delegate1._targets;
            var object = null;
            var method;
            if (delegate2._targets) {
                object = delegate2._targets[0];
                method = delegate2._targets[1]
            } else {
                method = delegate2
            }
            for (var i = 0; i < targets.length; i += 2) {
                if ((targets[i] === object) && (targets[i + 1] === method)) {
                    if (targets.length == 2) {
                        return null
                    }
                    var t = ss.arrayClone(targets);
                    t.splice(i, 2);
                    return ss._mkdel(t)
                }
            }
            return delegate1
        };
        ss.delegateEquals = function ss$delegateEquals(a, b) {
            if (a === b)return true;
            if (!a._targets && !b._targets)return false;
            var ta = a._targets || [null, a], tb = b._targets || [null, b];
            if (ta.length != tb.length)return false;
            for (var i = 0; i < ta.length; i++) {
                if (ta[i] !== tb[i])return false
            }
            return true
        };
        var ss_Enum = function Enum$() {
        };
        ss_Enum.__typeName = 'ss.Enum';
        ss.Enum = ss_Enum;
        ss.initClass(ss_Enum, ss, {});
        ss_Enum.getValues = function Enum$getValues(enumType) {
            var parts = [];
            var values = enumType.prototype;
            for (var i in values) {
                if (values.hasOwnProperty(i)) parts.push(values[i])
            }
            return parts
        };
        var ss_IEnumerator = function IEnumerator$() {
        };
        ss_IEnumerator.__typeName = 'ss.IEnumerator';
        ss.IEnumerator = ss_IEnumerator;
        ss.initInterface(ss_IEnumerator, ss, {current: null, moveNext: null, reset: null}, [ss_IDisposable]);
        var ss_IEnumerable = function IEnumerable$() {
        };
        ss_IEnumerable.__typeName = 'ss.IEnumerable';
        ss.IEnumerable = ss_IEnumerable;
        ss.initInterface(ss_IEnumerable, ss, {getEnumerator: null});
        ss.getEnumerator = function ss$getEnumerator(obj) {
            return obj.getEnumerator ? obj.getEnumerator() : new ss_ArrayEnumerator(obj)
        };
        var ss_ICollection = function ICollection$() {
        };
        ss_ICollection.__typeName = 'ss.ICollection';
        ss.ICollection = ss_ICollection;
        ss.initInterface(ss_ICollection, ss, {get_count: null, add: null, clear: null, contains: null, remove: null});
        ss.count = function ss$count(obj) {
            return obj.get_count ? obj.get_count() : obj.length
        };
        ss.add = function ss$add(obj, item) {
            if (obj.add) obj.add(item); else if (ss.isArray(obj)) obj.push(item); else throw new ss_NotSupportedException
        };
        ss.clear = function ss$clear(obj) {
            if (obj.clear) obj.clear(); else if (ss.isArray(obj)) obj.length = 0; else throw new ss_NotSupportedException
        };
        ss.remove = function ss$remove(obj, item) {
            if (obj.remove)return obj.remove(item); else if (ss.isArray(obj)) {
                var index = ss.indexOf(obj, item);
                if (index >= 0) {
                    obj.splice(index, 1);
                    return true
                }
                return false
            } else throw new ss_NotSupportedException
        };
        ss.contains = function ss$contains(obj, item) {
            if (obj.contains)return obj.contains(item); else return ss.indexOf(obj, item) >= 0
        };
        var ss_IEqualityComparer = function IEqualityComparer$() {
        };
        ss_IEqualityComparer.__typeName = 'ss.IEqualityComparer';
        ss.IEqualityComparer = ss_IEqualityComparer;
        ss.initInterface(ss_IEqualityComparer, ss, {areEqual: null, getObjectHashCode: null});
        var ss_IComparer = function IComparer$() {
        };
        ss_IComparer.__typeName = 'ss.IComparer';
        ss.IComparer = ss_IComparer;
        ss.initInterface(ss_IComparer, ss, {compare: null});
        ss.unbox = function ss$unbox(instance) {
            if (!ss.isValue(instance))throw new ss_InvalidOperationException('Nullable object must have a value.');
            return instance
        };
        var ss_Nullable$1 = function Nullable$1$(T) {
            var $type = function () {
            };
            $type.isInstanceOfType = function (instance) {
                return ss.isInstanceOfType(instance, T)
            };
            ss.registerGenericClassInstance($type, ss_Nullable$1, [T], {}, function () {
                return null
            }, function () {
                return []
            });
            return $type
        };
        ss_Nullable$1.__typeName = 'ss.Nullable$1';
        ss.Nullable$1 = ss_Nullable$1;
        ss.initGenericClass(ss_Nullable$1, ss, 1);
        ss_Nullable$1.eq = function Nullable$eq(a, b) {
            return !ss.isValue(a) ? !ss.isValue(b) : (a === b)
        };
        ss_Nullable$1.ne = function Nullable$eq(a, b) {
            return !ss.isValue(a) ? ss.isValue(b) : (a !== b)
        };
        ss_Nullable$1.le = function Nullable$le(a, b) {
            return ss.isValue(a) && ss.isValue(b) && a <= b
        };
        ss_Nullable$1.ge = function Nullable$ge(a, b) {
            return ss.isValue(a) && ss.isValue(b) && a >= b
        };
        ss_Nullable$1.lt = function Nullable$lt(a, b) {
            return ss.isValue(a) && ss.isValue(b) && a < b
        };
        ss_Nullable$1.gt = function Nullable$gt(a, b) {
            return ss.isValue(a) && ss.isValue(b) && a > b
        };
        ss_Nullable$1.sub = function Nullable$sub(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a - b : null
        };
        ss_Nullable$1.add = function Nullable$add(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a + b : null
        };
        ss_Nullable$1.mod = function Nullable$mod(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a % b : null
        };
        ss_Nullable$1.div = function Nullable$divf(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a / b : null
        };
        ss_Nullable$1.mul = function Nullable$mul(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a * b : null
        };
        ss_Nullable$1.band = function Nullable$band(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a & b : null
        };
        ss_Nullable$1.bor = function Nullable$bor(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a | b : null
        };
        ss_Nullable$1.xor = function Nullable$xor(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a ^ b : null
        };
        ss_Nullable$1.shl = function Nullable$shl(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a << b : null
        };
        ss_Nullable$1.srs = function Nullable$srs(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a >> b : null
        };
        ss_Nullable$1.sru = function Nullable$sru(a, b) {
            return ss.isValue(a) && ss.isValue(b) ? a >>> b : null
        };
        ss_Nullable$1.and = function Nullable$and(a, b) {
            if (a === true && b === true)return true; else if (a === false || b === false)return false; else return null
        };
        ss_Nullable$1.or = function Nullable$or(a, b) {
            if (a === true || b === true)return true; else if (a === false && b === false)return false; else return null
        };
        ss_Nullable$1.not = function Nullable$not(a) {
            return ss.isValue(a) ? !a : null
        };
        ss_Nullable$1.neg = function Nullable$neg(a) {
            return ss.isValue(a) ? -a : null
        };
        ss_Nullable$1.pos = function Nullable$pos(a) {
            return ss.isValue(a) ? +a : null
        };
        ss_Nullable$1.cpl = function Nullable$cpl(a) {
            return ss.isValue(a) ? ~a : null
        };
        ss_Nullable$1.lift = function Nullable$lift() {
            for (var i = 0; i < arguments.length; i++) {
                if (!ss.isValue(arguments[i]))return null
            }
            return arguments[0].apply(null, Array.prototype.slice.call(arguments, 1))
        };
        var ss_IList = function IList$() {
        };
        ss_IList.__typeName = 'ss.IList';
        ss.IList = ss_IList;
        ss.initInterface(ss_IList, ss, {get_item: null, set_item: null, indexOf: null, insert: null, removeAt: null}, [ss_ICollection, ss_IEnumerable]);
        ss.getItem = function ss$getItem(obj, index) {
            return obj.get_item ? obj.get_item(index) : obj[index]
        };
        ss.setItem = function ss$setItem(obj, index, value) {
            obj.set_item ? obj.set_item(index, value) : (obj[index] = value)
        };
        ss.indexOf = function ss$indexOf(obj, item) {
            var itemType = typeof(item);
            if ((!item || typeof(item.equals) !== 'function') && typeof(obj.indexOf) === 'function') {
                return obj.indexOf(item)
            } else if (ss.isArrayOrTypedArray(obj)) {
                for (var i = 0; i < obj.length; i++) {
                    if (ss.staticEquals(obj[i], item)) {
                        return i
                    }
                }
                return -1
            } else return obj.indexOf(item)
        };
        ss.insert = function ss$insert(obj, index, item) {
            if (obj.insert) obj.insert(index, item); else if (ss.isArray(obj)) obj.splice(index, 0, item); else throw new ss_NotSupportedException
        };
        ss.removeAt = function ss$removeAt(obj, index) {
            if (obj.removeAt) obj.removeAt(index); else if (ss.isArray(obj)) obj.splice(index, 1); else throw new ss_NotSupportedException
        };
        var ss_IDictionary = function IDictionary$() {
        };
        ss_IDictionary.__typeName = 'ss.IDictionary';
        ss.IDictionary = ss_IDictionary;
        ss.initInterface(ss_IDictionary, ss, {
            get_item: null,
            set_item: null,
            get_keys: null,
            get_values: null,
            containsKey: null,
            add: null,
            remove: null,
            tryGetValue: null
        }, [ss_IEnumerable]);
        var ss_Int32 = function Int32$() {
        };
        ss_Int32.__typeName = 'ss.Int32';
        ss.Int32 = ss_Int32;
        ss.initClass(ss_Int32, ss, {}, Object, [ss_IEquatable, ss_IComparable, ss_IFormattable]);
        ss_Int32.__class = false;
        ss_Int32.isInstanceOfType = function Int32$isInstanceOfType(instance) {
            return typeof(instance) === 'number' && isFinite(instance) && Math.round(instance, 0) == instance
        };
        ss_Int32.getDefaultValue = ss_Int32.createInstance = function Int32$getDefaultValue() {
            return 0
        };
        ss_Int32.div = function Int32$div(a, b) {
            if (!ss.isValue(a) || !ss.isValue(b))return null;
            if (b === 0)throw new ss_DivideByZeroException;
            return ss_Int32.trunc(a / b)
        };
        ss_Int32.trunc = function Int32$trunc(n) {
            return ss.isValue(n) ? (n > 0 ? Math.floor(n) : Math.ceil(n)) : null
        };
        ss_Int32.tryParse = function Int32$tryParse(s, result, min, max) {
            result.$ = 0;
            if (!/^[+-]?[0-9]+$/.test(s))return 0;
            var n = parseInt(s, 10);
            if (n < min || n > max)return false;
            result.$ = n;
            return true
        };
        var ss_JsDate = function JsDate$() {
        };
        ss_JsDate.__typeName = 'ss.JsDate';
        ss.JsDate = ss_JsDate;
        ss.initClass(ss_JsDate, ss, {}, Object, [ss_IEquatable, ss_IComparable]);
        ss_JsDate.createInstance = function JsDate$createInstance() {
            return new Date
        };
        ss_JsDate.isInstanceOfType = function JsDate$isInstanceOfType(instance) {
            return instance instanceof Date
        };
        var ss_ArrayEnumerator = function ArrayEnumerator$(array) {
            this._array = array;
            this._index = -1
        };
        ss_ArrayEnumerator.__typeName = 'ss.ArrayEnumerator';
        ss.ArrayEnumerator = ss_ArrayEnumerator;
        ss.initClass(ss_ArrayEnumerator, ss, {
            moveNext: function ArrayEnumerator$moveNext() {
                this._index++;
                return (this._index < this._array.length)
            }, reset: function ArrayEnumerator$reset() {
                this._index = -1
            }, current: function ArrayEnumerator$current() {
                if (this._index < 0 || this._index >= this._array.length)throw'Invalid operation';
                return this._array[this._index]
            }, dispose: function ArrayEnumerator$dispose() {
            }
        }, null, [ss_IEnumerator, ss_IDisposable]);
        var ss_ObjectEnumerator = function ObjectEnumerator$(o) {
            this._keys = Object.keys(o);
            this._index = -1;
            this._object = o
        };
        ss_ObjectEnumerator.__typeName = 'ss.ObjectEnumerator';
        ss.ObjectEnumerator = ss_ObjectEnumerator;
        ss.initClass(ss_ObjectEnumerator, ss, {
            moveNext: function ObjectEnumerator$moveNext() {
                this._index++;
                return (this._index < this._keys.length)
            }, reset: function ObjectEnumerator$reset() {
                this._index = -1
            }, current: function ObjectEnumerator$current() {
                if (this._index < 0 || this._index >= this._keys.length)throw new ss_InvalidOperationException('Invalid operation');
                var k = this._keys[this._index];
                return {key: k, value: this._object[k]}
            }, dispose: function ObjectEnumerator$dispose() {
            }
        }, null, [ss_IEnumerator, ss_IDisposable]);
        var ss_EqualityComparer = function EqualityComparer$() {
        };
        ss_EqualityComparer.__typeName = 'ss.EqualityComparer';
        ss.EqualityComparer = ss_EqualityComparer;
        ss.initClass(ss_EqualityComparer, ss, {
            areEqual: function EqualityComparer$areEqual(x, y) {
                return ss.staticEquals(x, y)
            }, getObjectHashCode: function EqualityComparer$getObjectHashCode(obj) {
                return ss.isValue(obj) ? ss.getHashCode(obj) : 0
            }
        }, null, [ss_IEqualityComparer]);
        ss_EqualityComparer.def = new ss_EqualityComparer;
        var ss_Comparer = function Comparer$(f) {
            this.f = f
        };
        ss_Comparer.__typeName = 'ss.Comparer';
        ss.Comparer = ss_Comparer;
        ss.initClass(ss_Comparer, ss, {
            compare: function Comparer$compare(x, y) {
                return this.f(x, y)
            }
        }, null, [ss_IComparer]);
        ss_Comparer.def = new ss_Comparer(function Comparer$defaultCompare(a, b) {
            if (!ss.isValue(a))return !ss.isValue(b) ? 0 : -1; else if (!ss.isValue(b))return 1; else return ss.compare(a, b)
        });
        var ss_IDisposable = function IDisposable$() {
        };
        ss_IDisposable.__typeName = 'ss.IDisposable';
        ss.IDisposable = ss_IDisposable;
        ss.initInterface(ss_IDisposable, ss, {dispose: null});
        var ss_StringBuilder = function StringBuilder$(s) {
            this._parts = (ss.isValue(s) && s != '') ? [s] : [];
            this.length = ss.isValue(s) ? s.length : 0
        };
        ss_StringBuilder.__typeName = 'ss.StringBuilder';
        ss.StringBuilder = ss_StringBuilder;
        ss.initClass(ss_StringBuilder, ss, {
            append: function StringBuilder$append(o) {
                if (ss.isValue(o)) {
                    var s = o.toString();
                    ss.add(this._parts, s);
                    this.length += s.length
                }
                return this
            }, appendChar: function StringBuilder$appendChar(c) {
                return this.append(String.fromCharCode(c))
            }, appendLine: function StringBuilder$appendLine(s) {
                this.append(s);
                this.append('\r\n');
                return this
            }, appendLineChar: function StringBuilder$appendLineChar(c) {
                return this.appendLine(String.fromCharCode(c))
            }, clear: function StringBuilder$clear() {
                this._parts = [];
                this.length = 0
            }, toString: function StringBuilder$toString() {
                return this._parts.join('')
            }
        });
        var ss_EventArgs = function EventArgs$() {
        };
        ss_EventArgs.__typeName = 'ss.EventArgs';
        ss.EventArgs = ss_EventArgs;
        ss.initClass(ss_EventArgs, ss, {});
        ss_EventArgs.Empty = new ss_EventArgs;
        var ss_Exception = function Exception$(message, innerException) {
            this._message = message || 'An error occurred.';
            this._innerException = innerException || null;
            this._error = new Error
        };
        ss_Exception.__typeName = 'ss.Exception';
        ss.Exception = ss_Exception;
        ss.initClass(ss_Exception, ss, {
            get_message: function Exception$get_message() {
                return this._message
            }, get_innerException: function Exception$get_innerException() {
                return this._innerException
            }, get_stack: function Exception$get_stack() {
                return this._error.stack
            }, toString: function Exception$toString() {
                var message = this._message;
                var exception = this;
                if (ss.isNullOrEmptyString(message)) {
                    if (ss.isValue(ss.getInstanceType(exception)) && ss.isValue(ss.getTypeFullName(ss.getInstanceType(exception)))) {
                        message = ss.getTypeFullName(ss.getInstanceType(exception))
                    } else {
                        message = '[object Exception]'
                    }
                }
                return message
            }
        });
        ss_Exception.wrap = function Exception$wrap(o) {
            if (ss.isInstanceOfType(o, ss_Exception)) {
                return o
            } else if (o instanceof TypeError) {
                return new ss_NullReferenceException(o.message, new ss_JsErrorException(o))
            } else if (o instanceof RangeError) {
                return new ss_ArgumentOutOfRangeException(null, o.message, new ss_JsErrorException(o))
            } else if (o instanceof Error) {
                return new ss_JsErrorException(o)
            } else {
                return new ss_Exception(o.toString())
            }
        };
        var ss_NotImplementedException = function NotImplementedException$(message, innerException) {
            ss_Exception.call(this, message || 'The method or operation is not implemented.', innerException)
        };
        ss_NotImplementedException.__typeName = 'ss.NotImplementedException';
        ss.NotImplementedException = ss_NotImplementedException;
        ss.initClass(ss_NotImplementedException, ss, {}, ss_Exception);
        var ss_NotSupportedException = function NotSupportedException$(message, innerException) {
            ss_Exception.call(this, message || 'Specified method is not supported.', innerException)
        };
        ss_NotSupportedException.__typeName = 'ss.NotSupportedException';
        ss.NotSupportedException = ss_NotSupportedException;
        ss.initClass(ss_NotSupportedException, ss, {}, ss_Exception);
        var ss_AggregateException = function AggregateException$(message, innerExceptions) {
            this.innerExceptions = ss.isValue(innerExceptions) ? ss.arrayFromEnumerable(innerExceptions) : [];
            ss_Exception.call(this, message || 'One or more errors occurred.', this.innerExceptions.length ? this.innerExceptions[0] : null)
        };
        ss_AggregateException.__typeName = 'ss.AggregateException';
        ss.AggregateException = ss_AggregateException;
        ss.initClass(ss_AggregateException, ss, {
            flatten: function AggregateException$flatten() {
                var inner = [];
                for (var i = 0; i < this.innerExceptions.length; i++) {
                    var e = this.innerExceptions[i];
                    if (ss.isInstanceOfType(e, ss_AggregateException)) {
                        inner.push.apply(inner, e.flatten().innerExceptions)
                    } else {
                        inner.push(e)
                    }
                }
                return new ss_AggregateException(this._message, inner)
            }
        }, ss_Exception);
        var ss_PromiseException = function PromiseException(args, message, innerException) {
            ss_Exception.call(this, message || (args.length && args[0] ? args[0].toString() : 'An error occurred'), innerException);
            this.arguments = ss.arrayClone(args)
        };
        ss_PromiseException.__typeName = 'ss.PromiseException';
        ss.PromiseException = ss_PromiseException;
        ss.initClass(ss_PromiseException, ss, {
            get_arguments: function PromiseException$get_arguments() {
                return this._arguments
            }
        }, ss_Exception);
        var ss_JsErrorException = function JsErrorException$(error, message, innerException) {
            ss_Exception.call(this, message || error.message, innerException);
            this.error = error
        };
        ss_JsErrorException.__typeName = 'ss.JsErrorException';
        ss.JsErrorException = ss_JsErrorException;
        ss.initClass(ss_JsErrorException, ss, {
            get_stack: function Exception$get_stack() {
                return this.error.stack
            }
        }, ss_Exception);
        var ss_ArgumentException = function ArgumentException$(message, paramName, innerException) {
            ss_Exception.call(this, message || 'Value does not fall within the expected range.', innerException);
            this.paramName = paramName || null
        };
        ss_ArgumentException.__typeName = 'ss.ArgumentException';
        ss.ArgumentException = ss_ArgumentException;
        ss.initClass(ss_ArgumentException, ss, {}, ss_Exception);
        var ss_ArgumentNullException = function ArgumentNullException$(paramName, message, innerException) {
            if (!message) {
                message = 'Value cannot be null.';
                if (paramName) message += '\nParameter name: ' + paramName
            }
            ss_ArgumentException.call(this, message, paramName, innerException)
        };
        ss_ArgumentNullException.__typeName = 'ss.ArgumentNullException';
        ss.ArgumentNullException = ss_ArgumentNullException;
        ss.initClass(ss_ArgumentNullException, ss, {}, ss_ArgumentException);
        var ss_ArgumentOutOfRangeException = function ArgumentOutOfRangeException$(paramName, message, innerException, actualValue) {
            if (!message) {
                message = 'Value is out of range.';
                if (paramName) message += '\nParameter name: ' + paramName
            }
            ss_ArgumentException.call(this, message, paramName, innerException);
            this.actualValue = actualValue || null
        };
        ss_ArgumentOutOfRangeException.__typeName = 'ss.ArgumentOutOfRangeException';
        ss.ArgumentOutOfRangeException = ss_ArgumentOutOfRangeException;
        ss.initClass(ss_ArgumentOutOfRangeException, ss, {}, ss_ArgumentException);
        var ss_FormatException = function FormatException$(message, innerException) {
            ss_Exception.call(this, message || 'Invalid format.', innerException)
        };
        ss_FormatException.__typeName = 'ss.FormatException';
        ss.FormatException = ss_FormatException;
        ss.initClass(ss_FormatException, ss, {}, ss_Exception);
        var ss_DivideByZeroException = function DivideByZeroException$(message, innerException) {
            ss_Exception.call(this, message || 'Division by 0.', innerException)
        };
        ss_DivideByZeroException.__typeName = 'ss.DivideByZeroException';
        ss.DivideByZeroException = ss_DivideByZeroException;
        ss.initClass(ss_DivideByZeroException, ss, {}, ss_Exception);
        var ss_InvalidCastException = function InvalidCastException$(message, innerException) {
            ss_Exception.call(this, message || 'The cast is not valid.', innerException)
        };
        ss_InvalidCastException.__typeName = 'ss.InvalidCastException';
        ss.InvalidCastException = ss_InvalidCastException;
        ss.initClass(ss_InvalidCastException, ss, {}, ss_Exception);
        var ss_InvalidOperationException = function InvalidOperationException$(message, innerException) {
            ss_Exception.call(this, message || 'Operation is not valid due to the current state of the object.', innerException)
        };
        ss_InvalidOperationException.__typeName = 'ss.InvalidOperationException';
        ss.InvalidOperationException = ss_InvalidOperationException;
        ss.initClass(ss_InvalidOperationException, ss, {}, ss_Exception);
        var ss_NullReferenceException = function NullReferenceException$(message, innerException) {
            ss_Exception.call(this, message || 'Object is null.', innerException)
        };
        ss_NullReferenceException.__typeName = 'ss.NullReferenceException';
        ss.NullReferenceException = ss_NullReferenceException;
        ss.initClass(ss_NullReferenceException, ss, {}, ss_Exception);
        var ss_KeyNotFoundException = function KeyNotFoundException$(message, innerException) {
            ss_Exception.call(this, message || 'Key not found.', innerException)
        };
        ss_KeyNotFoundException.__typeName = 'ss.KeyNotFoundException';
        ss.KeyNotFoundException = ss_KeyNotFoundException;
        ss.initClass(ss_KeyNotFoundException, ss, {}, ss_Exception);
        var ss_AmbiguousMatchException = function AmbiguousMatchException$(message, innerException) {
            ss_Exception.call(this, message || 'Ambiguous match.', innerException)
        };
        ss_AmbiguousMatchException.__typeName = 'ss.AmbiguousMatchException';
        ss.AmbiguousMatchException = ss_AmbiguousMatchException;
        ss.initClass(ss_AmbiguousMatchException, ss, {}, ss_Exception);
        var ss_IteratorBlockEnumerable = function IteratorBlockEnumerable$(getEnumerator, $this) {
            this._getEnumerator = getEnumerator;
            this._this = $this
        };
        ss_IteratorBlockEnumerable.__typeName = 'ss.IteratorBlockEnumerable';
        ss.IteratorBlockEnumerable = ss_IteratorBlockEnumerable;
        ss.initClass(ss_IteratorBlockEnumerable, ss, {
            getEnumerator: function IteratorBlockEnumerable$getEnumerator() {
                return this._getEnumerator.call(this._this)
            }
        }, null, [ss_IEnumerable]);
        var ss_IteratorBlockEnumerator = function IteratorBlockEnumerator$(moveNext, getCurrent, dispose, $this) {
            this._moveNext = moveNext;
            this._getCurrent = getCurrent;
            this._dispose = dispose;
            this._this = $this
        };
        ss_IteratorBlockEnumerator.__typeName = 'ss.IteratorBlockEnumerator';
        ss.IteratorBlockEnumerator = ss_IteratorBlockEnumerator;
        ss.initClass(ss_IteratorBlockEnumerator, ss, {
            moveNext: function IteratorBlockEnumerator$moveNext() {
                try {
                    return this._moveNext.call(this._this)
                } catch (ex) {
                    if (this._dispose) this._dispose.call(this._this);
                    throw ex
                }
            }, current: function IteratorBlockEnumerator$current() {
                return this._getCurrent.call(this._this)
            }, reset: function IteratorBlockEnumerator$reset() {
                throw new ss_NotSupportedException('Reset is not supported.')
            }, dispose: function IteratorBlockEnumerator$dispose() {
                if (this._dispose) this._dispose.call(this._this)
            }
        }, null, [ss_IEnumerator, ss_IDisposable]);
        var ss_Lazy = function Lazy$(valueFactory) {
            this._valueFactory = valueFactory;
            this.isValueCreated = false
        };
        ss_Lazy.__typeName = 'ss.Lazy';
        ss.Lazy = ss_Lazy;
        ss.initClass(ss_Lazy, ss, {
            value: function Lazy$value() {
                if (!this.isValueCreated) {
                    this._value = this._valueFactory();
                    delete this._valueFactory;
                    this.isValueCreated = true
                }
                return this._value
            }
        });
        if (typeof(global.HTMLElement) === 'undefined') {
            global.HTMLElement = Element
        }
        if (typeof(global.MessageEvent) === 'undefined') {
            global.MessageEvent = Event
        }
        Date.now = Date.now || function () {
                return +new Date
            };
        global.ss = ss
    })(global);
    var ss = global.ss;
    var HTMLElement = global.HTMLElement;
    var MessageEvent = global.MessageEvent;
    /*! BEGIN CoreSlim */
    (function () {
        'dont use strict';
        var a = {};
        global.tab = global.tab || {};
        ss.initAssembly(a, 'tabcoreslim');
        var b = function () {
        };
        b.__typeName = 'tab.EscapingUtil';
        b.escapeHtml = function (e) {
            var f = ss.coalesce(e, '');
            f = f.replace(new RegExp('&', 'g'), '&amp;');
            f = f.replace(new RegExp('<', 'g'), '&lt;');
            f = f.replace(new RegExp('>', 'g'), '&gt;');
            f = f.replace(new RegExp('"', 'g'), '&quot;');
            f = f.replace(new RegExp("'", 'g'), '&#39;');
            f = f.replace(new RegExp('/', 'g'), '&#47;');
            return f
        };
        global.tab.EscapingUtil = b;
        var c = function () {
        };
        c.__typeName = 'tab.ScriptEx';
        global.tab.ScriptEx = c;
        var d = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        d.__typeName = 'tab.WindowHelper';
        d.get_windowSelf = function () {
            return window.self
        };
        d.get_selection = function () {
            if (typeof(window['getSelection']) === 'function') {
                return window.getSelection()
            } else if (typeof(document['getSelection']) === 'function') {
                return document.getSelection()
            }
            return null
        };
        d.close = function (e) {
            e.close()
        };
        d.getOpener = function (e) {
            return e.opener
        };
        d.getLocation = function (e) {
            return e.location
        };
        d.getPathAndSearch = function (e) {
            return e.location.pathname + e.location.search
        };
        d.setLocationHref = function (e, f) {
            e.location.href = f
        };
        d.locationReplace = function (e, f) {
            e.location.replace(f)
        };
        d.open = function (e, f, g) {
            return window.open(e, f, g)
        };
        d.reload = function (e, f) {
            e.location.reload(f)
        };
        d.requestAnimationFrame = function (e) {
            return d.$c(e)
        };
        d.cancelAnimationFrame = function (e) {
            if (ss.isValue(e)) {
                d.$b(e)
            }
        };
        d.setTimeout = function (e, f) {
            return window.setTimeout(e, f)
        };
        d.addListener = function (e, f, g) {
            if ('addEventListener' in e) {
                e.addEventListener(f, g, false)
            } else {
                e.attachEvent('on' + f, g)
            }
        };
        d.removeListener = function (e, f, g) {
            if ('removeEventListener' in e) {
                e.removeEventListener(f, g, false)
            } else {
                e.detachEvent('on' + f, g)
            }
        };
        d.$0 = function () {
            var e = 0;
            d.$c = function (f) {
                var g = (new Date).getTime();
                var h = Math.max(0, 16 - (g - e));
                e = g + h;
                var i = window.setTimeout(f, h);
                return i
            }
        };
        d.clearSelection = function () {
            var e = d.get_selection();
            if (ss.isValue(e)) {
                if (typeof(e['removeAllRanges']) === 'function') {
                    e.removeAllRanges()
                } else if (typeof(e['empty']) === 'function') {
                    e['empty']()
                }
            }
        };
        global.tab.WindowHelper = d;
        ss.initClass(b, a, {});
        ss.initClass(c, a, {});
        ss.initClass(d, a, {
            get_pageXOffset: function () {
                return d.$7(this.$0)
            }, get_pageYOffset: function () {
                return d.$8(this.$0)
            }, get_clientWidth: function () {
                return d.$2(this.$0)
            }, get_clientHeight: function () {
                return d.$1(this.$0)
            }, get_innerWidth: function () {
                return d.$4(this.$0)
            }, get_outerWidth: function () {
                return d.$6(this.$0)
            }, get_innerHeight: function () {
                return d.$3(this.$0)
            }, get_outerHeight: function () {
                return d.$5(this.$0)
            }, get_screenLeft: function () {
                return d.$9(this.$0)
            }, get_screenTop: function () {
                return d.$a(this.$0)
            }, isQuirksMode: function () {
                return document.compatMode === 'BackCompat'
            }
        });
        (function () {
            d.$4 = null;
            d.$3 = null;
            d.$2 = null;
            d.$1 = null;
            d.$7 = null;
            d.$8 = null;
            d.$9 = null;
            d.$a = null;
            d.$6 = null;
            d.$5 = null;
            d.$c = null;
            d.$b = null;
            if ('innerWidth' in window) {
                d.$4 = function (m) {
                    return m.innerWidth
                }
            } else {
                d.$4 = function (m) {
                    return m.document.documentElement.offsetWidth
                }
            }
            if ('outerWidth' in window) {
                d.$6 = function (m) {
                    return m.outerWidth
                }
            } else {
                d.$6 = d.$4
            }
            if ('innerHeight' in window) {
                d.$3 = function (m) {
                    return m.innerHeight
                }
            } else {
                d.$3 = function (m) {
                    return m.document.documentElement.offsetHeight
                }
            }
            if ('outerHeight' in window) {
                d.$5 = function (m) {
                    return m.outerHeight
                }
            } else {
                d.$5 = d.$3
            }
            if ('clientWidth' in window) {
                d.$2 = function (m) {
                    return m['clientWidth']
                }
            } else {
                d.$2 = function (m) {
                    return m.document.documentElement.clientWidth
                }
            }
            if ('clientHeight' in window) {
                d.$1 = function (m) {
                    return m['clientHeight']
                }
            } else {
                d.$1 = function (m) {
                    return m.document.documentElement.clientHeight
                }
            }
            if (ss.isValue(window.self.pageXOffset)) {
                d.$7 = function (m) {
                    return m.pageXOffset
                }
            } else {
                d.$7 = function (m) {
                    return m.document.documentElement.scrollLeft
                }
            }
            if (ss.isValue(window.self.pageYOffset)) {
                d.$8 = function (m) {
                    return m.pageYOffset
                }
            } else {
                d.$8 = function (m) {
                    return m.document.documentElement.scrollTop
                }
            }
            if ('screenLeft' in window) {
                d.$9 = function (m) {
                    return m.screenLeft
                }
            } else {
                d.$9 = function (m) {
                    return m.screenX
                }
            }
            if ('screenTop' in window) {
                d.$a = function (m) {
                    return m.screenTop
                }
            } else {
                d.$a = function (m) {
                    return m.screenY
                }
            }
            {
                var e = 'requestAnimationFrame';
                var f = 'cancelAnimationFrame';
                var g = ['ms', 'moz', 'webkit', 'o'];
                var h = null;
                var i = null;
                if (e in window) {
                    h = e
                }
                if (f in window) {
                    i = f
                }
                for (var j = 0; j < g.length && (ss.isNullOrUndefined(h) || ss.isNullOrUndefined(i)); ++j) {
                    var k = g[j];
                    var l = k + 'RequestAnimationFrame';
                    if (ss.isNullOrUndefined(h) && l in window) {
                        h = l
                    }
                    if (ss.isNullOrUndefined(i)) {
                        l = k + 'CancelAnimationFrame';
                        if (l in window) {
                            i = l
                        }
                        l = k + 'CancelRequestAnimationFrame';
                        if (l in window) {
                            i = l
                        }
                    }
                }
                if (ss.isValue(h)) {
                    d.$c = function (m) {
                        return window[h](m)
                    }
                } else {
                    d.$0()
                }
                if (ss.isValue(i)) {
                    d.$b = function (m) {
                        window[i](m)
                    }
                } else {
                    d.$b = function (m) {
                        window.clearTimeout(m)
                    }
                }
            }
        })()
    })();
    var tab = global.tab;
    /*! API */
    (function () {
        'dont use strict';
        var a = {};
        global.tab = global.tab || {};
        global.tableauSoftware = global.tableauSoftware || {};
        ss.initAssembly(a, 'Tableau.JavaScript.Vql.Api');
        var b = function () {
            this.$a = 0;
            this.$9 = {};
            this.$6 = {};
            this.$8 = {};
            this.$7 = {};
            if (K.hasWindowAddEventListener()) {
                window.addEventListener('message', ss.mkdel(this, this.$1), false)
            } else if (K.hasDocumentAttachEvent()) {
                var e = ss.mkdel(this, this.$1);
                document.attachEvent('onmessage', e);
                window.attachEvent('onmessage', e)
            } else {
                window.onmessage = ss.mkdel(this, this.$1)
            }
            this.$a = 0
        };
        b.__typeName = 'tab.$0';
        var c = function () {
            this.$2 = null;
            this.$1$1 = null;
            this.$1$2 = null
        };
        c.__typeName = 'tab.$1';
        var d = function (e, cf) {
            bm.call(this, e, cf)
        };
        d.__typeName = 'tab.$10';
        var f = function (e, cf) {
            this.$2 = null;
            bm.call(this, e, null);
            this.$2 = cf
        };
        f.__typeName = 'tab.$11';
        var g = function (e, cf) {
            this.$2 = null;
            bm.call(this, e, null);
            this.$2 = cf
        };
        g.__typeName = 'tab.$2';
        var h = function (e, cf, cg, ch) {
            this.$3 = null;
            this.$4 = null;
            bm.call(this, e, cf);
            this.$3 = cg;
            this.$4 = ch
        };
        h.__typeName = 'tab.$3';
        var i = function (e, cf) {
            bm.call(this, e, cf)
        };
        i.__typeName = 'tab.$4';
        var j = function () {
        };
        j.__typeName = 'tab.$5';
        var k = function () {
        };
        k.__typeName = 'tab.$6';
        k.$0 = function (e) {
            var cf;
            if (e instanceof tableauSoftware.Promise) {
                cf = e
            } else {
                if (ss.isValue(e) && typeof(e['valueOf']) === 'function') {
                    e = e['valueOf']()
                }
                if (k.$1(e)) {
                    var cg = new z;
                    e.then(ss.mkdel(cg, cg.resolve), ss.mkdel(cg, cg.reject));
                    cf = cg.get_promise()
                } else {
                    cf = k.$4(e)
                }
            }
            return cf
        };
        k.$2 = function (e) {
            return k.$0(e).then(function (cf) {
                return k.$3(cf)
            }, null)
        };
        k.$4 = function (cf) {
            var cg = new C(function (ch, ci) {
                try {
                    return k.$0((ss.isValue(ch) ? ch(cf) : cf))
                } catch (cj) {
                    var e = ss.Exception.wrap(cj);
                    return k.$3(e)
                }
            });
            return cg
        };
        k.$3 = function (cf) {
            var cg = new C(function (ch, ci) {
                try {
                    return (ss.isValue(ci) ? k.$0(ci(cf)) : k.$3(cf))
                } catch (cj) {
                    var e = ss.Exception.wrap(cj);
                    return k.$3(e)
                }
            });
            return cg
        };
        k.$1 = function (e) {
            return ss.isValue(e) && typeof(e['then']) === 'function'
        };
        var l = function (e) {
            this.$4 = null;
            this.$5 = new tab._Collection;
            this.$6 = 0;
            if (A.isArray(e)) {
                var cf = e;
                for (var cg = 0; cg < cf.length; cg++) {
                    var ch = cf[cg];
                    if (!ss.isValue(ch.fieldName)) {
                        throw J.createInvalidParameter('pair.fieldName')
                    }
                    if (!ss.isValue(ch.value)) {
                        throw J.createInvalidParameter('pair.value')
                    }
                    var ci = new bR(ch.fieldName, ch.value);
                    this.$5._add(ci.fieldName, ci)
                }
            } else {
                this.$6 = e
            }
        };
        l.__typeName = 'tab.$7';
        l.$0 = function (e) {
            var cf = new tab._Collection;
            if (ss.isNullOrUndefined(e) || K.isNullOrEmpty(e.marks)) {
                return cf
            }
            for (var cg = 0; cg < e.marks.length; cg++) {
                var ch = e.marks[cg];
                var ci = ch.tupleId;
                var cj = new bQ(ci);
                cf._add(ci.toString(), cj);
                for (var ck = 0; ck < ch.pairs.length; ck++) {
                    var cl = ch.pairs[ck];
                    var cm = K.convertRawValue(cl.value, cl.valueDataType);
                    var cn = new bR(cl.fieldName, cm);
                    cn.formattedValue = cl.formattedValue;
                    if (!cj.$0.$2()._has(cn.fieldName)) {
                        cj.$0.$0(cn)
                    }
                }
            }
            return cf
        };
        var m = function (e) {
            this.$i = null;
            this.$h = null;
            this.$c = null;
            this.$d = null;
            this.$b = null;
            this.$a = null;
            this.$g = null;
            this.$f = null;
            this.$j = null;
            this.$e = null;
            this.$h = e.name;
            this.$c = K.getDataValue(e.currentValue);
            this.$d = S.convertParameterDataType(e.dataType);
            this.$b = S.convertParameterAllowableValuesType(e.allowableValuesType);
            if (ss.isValue(e.allowableValues) && this.$b === 'list') {
                this.$a = [];
                for (var cf = 0; cf < e.allowableValues.length; cf++) {
                    var cg = e.allowableValues[cf];
                    this.$a.push(K.getDataValue(cg))
                }
            }
            if (this.$b === 'range') {
                this.$g = K.getDataValue(e.minValue);
                this.$f = K.getDataValue(e.maxValue);
                this.$j = e.stepSize;
                if ((this.$d === 'date' || this.$d === 'datetime') && ss.isValue(this.$j) && ss.isValue(e.dateStepPeriod)) {
                    this.$e = S.convertPeriodType(e.dateStepPeriod)
                }
            }
        };
        m.__typeName = 'tab.$8';
        var n = function () {
        };
        n.__typeName = 'tab.$9';
        n.$2 = function (e) {
            return function (cf, cg) {
                if (ss.isValue(cf)) {
                    var ch = cf.toString().toUpperCase();
                    var ci = ss.Enum.getValues(e);
                    for (var cj = 0; cj < ci.length; cj++) {
                        var ck = ci[cj];
                        var cl = ck.toUpperCase();
                        if (ss.referenceEquals(ch, cl)) {
                            cg.$ = ck;
                            return true
                        }
                    }
                }
                cg.$ = ss.getDefaultValue(e);
                return false
            }
        };
        n.$1 = function (e) {
            return function (cf, cg) {
                var ch = {};
                if (!n.$2(e).call(null, cf, ch)) {
                    throw J.createInvalidParameter(cg)
                }
                return ch.$
            }
        };
        n.$0 = function (e) {
            return function (cf) {
                var cg = {};
                var ch = n.$2(e).call(null, cf, cg);
                return ch
            }
        };
        var o = function () {
        };
        o.__typeName = 'tab._ApiBootstrap';
        o.initialize = function () {
            q.registerCrossDomainMessageRouter(function () {
                return new b
            })
        };
        global.tab._ApiBootstrap = o;
        var p = function (e, cf, cg, ch) {
            this.$1$1 = null;
            this.$1$2 = null;
            this.$1$3 = null;
            this.$1$4 = null;
            this.set_name(e);
            this.set_commandId(cf);
            this.set_hostId(cg);
            this.set_parameters(ch)
        };
        p.__typeName = 'tab._ApiCommand';
        p.generateNextCommandId = function () {
            var e = 'cmd' + p.$0;
            p.$0++;
            return e
        };
        p.parse = function (e) {
            var cf;
            var cg = e.indexOf(String.fromCharCode(44));
            if (cg < 0) {
                cf = e;
                return new p(cf, null, null, null)
            }
            cf = e.substr(0, cg);
            var ch;
            var ci = e.substr(cg + 1);
            cg = ci.indexOf(String.fromCharCode(44));
            if (cg < 0) {
                ch = ci;
                return new p(cf, ch, null, null)
            }
            ch = ci.substr(0, cg);
            var cj;
            var ck = ci.substr(cg + 1);
            cg = ck.indexOf(String.fromCharCode(44));
            if (cg < 0) {
                cj = ck;
                return new p(cf, ch, cj, null)
            }
            cj = ck.substr(0, cg);
            var cl = ck.substr(cg + 1);
            return new p(cf, ch, cj, cl)
        };
        global.tab._ApiCommand = p;
        var q = function () {
        };
        q.__typeName = 'tab._ApiObjectRegistry';
        q.registerCrossDomainMessageRouter = function (e) {
            return q.$3(br).call(null, e)
        };
        q.getCrossDomainMessageRouter = function () {
            return q.$2(br).call(null)
        };
        q.disposeCrossDomainMessageRouter = function () {
            q.$0(br).call(null)
        };
        q.$3 = function (e) {
            return function (cf) {
                if (ss.isNullOrUndefined(q.$4)) {
                    q.$4 = {}
                }
                var cg = ss.getTypeFullName(e);
                var ch = q.$4[cg];
                q.$4[cg] = cf;
                return ch
            }
        };
        q.$1 = function (e) {
            return function () {
                if (ss.isNullOrUndefined(q.$4)) {
                    throw J.createInternalError('No types registered')
                }
                var cf = ss.getTypeFullName(e);
                var cg = q.$4[cf];
                if (ss.isNullOrUndefined(cg)) {
                    throw J.createInternalError("No creation function has been registered for interface type '" + cf + "'.")
                }
                var ch = cg();
                return ch
            }
        };
        q.$2 = function (e) {
            return function () {
                if (ss.isNullOrUndefined(q.$5)) {
                    q.$5 = {}
                }
                var cf = ss.getTypeFullName(e);
                var cg = q.$5[cf];
                if (ss.isNullOrUndefined(cg)) {
                    cg = q.$1(e).call(null);
                    q.$5[cf] = cg
                }
                return cg
            }
        };
        q.$0 = function (e) {
            return function () {
                if (ss.isNullOrUndefined(q.$5)) {
                    return null
                }
                var cf = ss.getTypeFullName(e);
                var cg = q.$5[cf];
                delete q.$5[cf];
                return cg
            }
        };
        global.tab._ApiObjectRegistry = q;
        var r = function (e, cf, cg) {
            this.$1 = null;
            this.$2 = null;
            this.$0 = null;
            this.$1 = e;
            this.$2 = cf;
            this.$0 = cg
        };
        r.__typeName = 'tab._ApiServerNotification';
        r.deserialize = function (e) {
            var cf = JSON.parse(e);
            var cg = cf['api.workbookName'];
            var ch = cf['api.worksheetName'];
            var ci = cf['api.commandData'];
            return new r(cg, ch, ci)
        };
        global.tab._ApiServerNotification = r;
        var s = function (e) {
            this.$1 = null;
            this.$0 = null;
            var cf = JSON.parse(e);
            this.$1 = cf['api.commandResult'];
            this.$0 = cf['api.commandData']
        };
        s.__typeName = 'tab._ApiServerResultParser';
        global.tab._ApiServerResultParser = s;
        var t = function () {
            this.$4 = [];
            this.$3 = {}
        };
        t.__typeName = 'tab._CollectionImpl';
        global.tab._CollectionImpl = t;
        var u = function (e, cf, cg, ch) {
            this.$1 = null;
            this.$0 = null;
            this.$3 = false;
            this.$2 = 0;
            B.verifyString(e, 'Column Field Name');
            this.$1 = e;
            this.$0 = cf;
            this.$3 = ss.coalesce(cg, false);
            this.$2 = ch
        };
        u.__typeName = 'tab._ColumnImpl';
        global.tab._ColumnImpl = u;
        var v = function (e, cf, cg) {
            this.$c = null;
            this.$j = null;
            this.$l = null;
            this.$g = null;
            this.$h = null;
            this.$i = null;
            this.$k = null;
            this.$e = false;
            this.$d = false;
            this.$f = false;
            this.$l = e;
            this.$h = cf;
            this.$g = cg;
            this.$e = false;
            this.$d = false;
            this.$f = false
        };
        v.__typeName = 'tab._CustomViewImpl';
        v._getAsync = function (e) {
            var cf = new tab._Deferred;
            cf.resolve(e.get__customViewImpl().$5());
            return cf.get_promise()
        };
        v._createNew = function (e, cf, cg, ch) {
            var ci = new v(e, cg.name, cf);
            ci.$e = cg.isPublic;
            ci.$k = cg.url;
            ci.$i = cg.owner.friendlyName;
            ci.$d = ss.isValue(ch) && ss.unbox(ch) === cg.id;
            ci.$j = cg;
            return ci
        };
        v._saveNewAsync = function (e, cf, cg) {
            var ch = new tab._Deferred;
            var ci = {};
            ci['api.customViewName'] = cg;
            var cj = v.$0('api.SaveNewCustomViewCommand', ch, function (ck) {
                v._processCustomViewUpdate(e, cf, ck, true);
                var cl = null;
                if (ss.isValue(e.$p())) {
                    cl = e.$p().get_item(0)
                }
                ch.resolve(cl)
            });
            cf.sendCommand(Object).call(cf, ci, cj);
            return ch.get_promise()
        };
        v._showCustomViewAsync = function (e, cf, cg) {
            var ch = new tab._Deferred;
            var ci = {};
            if (ss.isValue(cg)) {
                ci['api.customViewParam'] = cg
            }
            var cj = v.$0('api.ShowCustomViewCommand', ch, function (ck) {
                var cl = e.get_activeCustomView();
                ch.resolve(cl)
            });
            cf.sendCommand(Object).call(cf, ci, cj);
            return ch.get_promise()
        };
        v._makeCurrentCustomViewDefaultAsync = function (e, cf) {
            var cg = new tab._Deferred;
            var ch = {};
            var ci = v.$0('api.MakeCurrentCustomViewDefaultCommand', cg, function (cj) {
                var ck = e.get_activeCustomView();
                cg.resolve(ck)
            });
            cf.sendCommand(Object).call(cf, ch, ci);
            return cg.get_promise()
        };
        v._getCustomViewsAsync = function (e, cf) {
            var cg = new tab._Deferred;
            var ch = new (ss.makeGenericType(bh, [Object]))('api.FetchCustomViewsCommand', 0, function (ci) {
                v._processCustomViews(e, cf, ci);
                cg.resolve(e.$i()._toApiCollection())
            }, function (ci, cj) {
                cg.reject(J.create('serverError', cj))
            });
            cf.sendCommand(Object).call(cf, null, ch);
            return cg.get_promise()
        };
        v._processCustomViews = function (e, cf, cg) {
            v._processCustomViewUpdate(e, cf, cg, false)
        };
        v._processCustomViewUpdate = function (e, cf, cg, ch) {
            if (ch) {
                e.$q(new tab._Collection)
            }
            e.$h(null);
            var ci = null;
            if (ss.isValue(cg.currentView)) {
                ci = cg.currentView.name
            }
            var cj = cg.defaultCustomViewId;
            if (ch && ss.isValue(cg.newView)) {
                var ck = v._createNew(e, cf, cg.newView, cj);
                e.$p()._add(ck.$7(), ck.$5())
            }
            e.$o(e.$i());
            e.$j(new tab._Collection);
            if (ss.isValue(cg.customViews)) {
                var cl = cg.customViews;
                if (cl.length > 0) {
                    for (var cm = 0; cm < cl.length; cm++) {
                        var cn = v._createNew(e, cf, cl[cm], cj);
                        e.$i()._add(cn.$7(), cn.$5());
                        if (e.$n()._has(cn.$7())) {
                            e.$n()._remove(cn.$7())
                        } else if (ch) {
                            if (!e.$p()._has(cn.$7())) {
                                e.$p()._add(cn.$7(), cn.$5())
                            }
                        }
                        if (ss.isValue(ci) && ss.referenceEquals(cn.$7(), ci)) {
                            e.$h(cn.$5())
                        }
                    }
                }
            }
        };
        v.$0 = function (e, cf, cg) {
            var ch = function (ci, cj) {
                cf.reject(J.create('serverError', cj))
            };
            return new (ss.makeGenericType(bh, [Object]))(e, 0, cg, ch)
        };
        var w = function (e, cf, cg) {
            this.$d = null;
            this.$f = new tab._Collection;
            this.$e = new tab._Collection;
            E.call(this, e, cf, cg)
        };
        w.__typeName = 'tab._DashboardImpl';
        global.tab._DashboardImpl = w;
        var x = function (e, cf) {
            this.$3 = null;
            this.$1 = new tab._Collection;
            this.$2 = false;
            this.$0 = null;
            B.verifyString(e, 'name');
            this.$3 = e;
            this.$2 = cf
        };
        x.__typeName = 'tab._DataSourceImpl';
        x.processDataSource = function (e) {
            var cf = new x(e.name, e.isPrimary);
            var cg = ss.coalesce(e.fields, []);
            for (var ch = 0; ch < cg.length; ch++) {
                var ci = cg[ch];
                var cj = S.convertFieldRole(ci.role);
                var ck = S.convertFieldAggregation(ci.aggregation);
                var cl = new bN(cf.get_dataSource(), ci.name, cj, ck);
                cf.addField(cl)
            }
            return cf
        };
        x.processDataSourcesForWorksheet = function (e) {
            var cf = new tab._Collection;
            var cg = null;
            for (var ch = 0; ch < e.dataSources.length; ch++) {
                var ci = e.dataSources[ch];
                var cj = x.processDataSource(ci);
                if (ci.isPrimary) {
                    cg = cj
                } else {
                    cf._add(ci.name, cj.get_dataSource())
                }
            }
            if (ss.isValue(cg)) {
                cf._addToFirst(cg.get_name(), cg.get_dataSource())
            }
            return cf
        };
        global.tab._DataSourceImpl = x;
        var y = function (e, cf, cg, ch) {
            this.$2 = null;
            this.$3 = null;
            this.$4 = 0;
            this.$0 = null;
            this.$1 = false;
            this.$3 = e;
            this.$4 = cg;
            this.$0 = ch;
            this.$1 = cf;
            this.$2 = (cf ? 'Summary Data Table' : 'Underlying Data Table')
        };
        y.__typeName = 'tab._DataTableImpl';
        y.processGetDataPresModel = function (e) {
            var cf = y.$1(e.dataTable);
            var cg = y.$0(e.headers);
            var ch = new y(cf, e.isSummary, cf.length, cg);
            return new bM(ch)
        };
        y.$1 = function (e) {
            var cf = [];
            for (var cg = 0; cg < e.length; cg++) {
                var ch = e[cg];
                var ci = [];
                for (var cj = 0; cj < ch.length; cj++) {
                    var ck = ch[cj];
                    ci.push(K.getDataValue(ck))
                }
                cf.push(ci)
            }
            return cf
        };
        y.$0 = function (e) {
            var cf = [];
            for (var cg = 0; cg < e.length; cg++) {
                var ch = e[cg];
                var ci = new u(ch.fieldName, S.convertDataType(ch.dataType), ch.isReferenced, ch.index);
                cf.push(new bH(ci))
            }
            return cf
        };
        global.tab._DataTableImpl = y;
        var z = function () {
            this.$3 = null;
            this.$5 = null;
            this.$2 = [];
            this.$4 = null;
            this.$3 = new C(ss.mkdel(this, this.then));
            this.$5 = ss.mkdel(this, this.$0);
            this.$4 = ss.mkdel(this, this.$1)
        };
        z.__typeName = 'tab._DeferredImpl';
        global.tab._DeferredImpl = z;
        var A = function () {
        };
        A.__typeName = 'tab._jQueryShim';
        A.isFunction = function (e) {
            return A.type(e) === 'function'
        };
        A.isArray = function (e) {
            if (ss.isValue(Array['isArray'])) {
                return Array['isArray'](e)
            }
            return A.type(e) === 'array'
        };
        A.type = function (e) {
            return (ss.isNullOrUndefined(e) ? String(e) : (A.$8[A.$d.call(e)] || 'object'))
        };
        A.trim = function (e) {
            if (ss.isValue(A.$e)) {
                return (ss.isNullOrUndefined(e) ? '' : A.$e.call(e))
            }
            return (ss.isNullOrUndefined(e) ? '' : e.toString().replace(A.$f, '').replace(A.$g, ''))
        };
        A.parseJSON = function (e) {
            if (typeof(e) !== 'string' || ss.isNullOrUndefined(e)) {
                return null
            }
            e = A.trim(e);
            if (ss.isValue(JSON) && ss.isValue(JSON['parse'])) {
                return JSON.parse(e)
            }
            if (A.$a.test(e.replace(A.$b, '@').replace(A.$c, ']').replace(A.$9, ''))) {
                return (new Function('return ' + e))()
            }
            throw new ss.Exception('Invalid JSON: ' + e)
        };
        global.tab._jQueryShim = A;
        var B = function () {
        };
        B.__typeName = 'tab._Param';
        B.verifyString = function (e, cf) {
            if (ss.isNullOrUndefined(e) || e.length === 0) {
                throw J.createInternalStringArgumentException(cf)
            }
        };
        B.verifyValue = function (e, cf) {
            if (ss.isNullOrUndefined(e)) {
                throw J.createInternalNullArgumentException(cf)
            }
        };
        global.tab._Param = B;
        var C = function (e) {
            this.then = null;
            this.then = e
        };
        C.__typeName = 'tab._PromiseImpl';
        global.tab._PromiseImpl = C;
        var D = function (e, cf, cg, ch) {
            this.left = 0;
            this.top = 0;
            this.width = 0;
            this.height = 0;
            this.left = e;
            this.top = cf;
            this.width = cg;
            this.height = ch
        };
        D.__typeName = 'tab._Rect';
        global.tab._Rect = D;
        var E = function (e, cf, cg) {
            this.$5 = null;
            this.$1 = 0;
            this.$2 = false;
            this.$3 = false;
            this.$7 = null;
            this.$8 = null;
            this.$9 = null;
            this.$a = null;
            this.$4 = null;
            this.$6 = null;
            this.$b = 0;
            B.verifyValue(e, 'sheetInfoImpl');
            B.verifyValue(cf, 'workbookImpl');
            B.verifyValue(cg, 'messagingOptions');
            this.$5 = e.name;
            this.$1 = e.index;
            this.$2 = e.isActive;
            this.$3 = e.isHidden;
            this.$7 = e.sheetType;
            this.$8 = e.size;
            this.$9 = e.url;
            this.$a = cf;
            this.$4 = cg;
            this.$b = e.zoneId
        };
        E.__typeName = 'tab._SheetImpl';
        E.$0 = function (e) {
            if (ss.isValue(e)) {
                return K.toInt(e)
            }
            return e
        };
        E.$1 = function (e) {
            var cf = n.$1(bd).call(null, e.behavior, 'size.behavior');
            var cg = e.minSize;
            if (ss.isValue(cg)) {
                cg = bx.$ctor(E.$0(e.minSize.width), E.$0(e.minSize.height))
            }
            var ch = e.maxSize;
            if (ss.isValue(ch)) {
                ch = bx.$ctor(E.$0(e.maxSize.width), E.$0(e.maxSize.height))
            }
            return bv.$ctor(cf, cg, ch)
        };
        global.tab._SheetImpl = E;
        var F = function () {
        };
        F.__typeName = 'tab._SheetInfoImpl';
        F.$ctor = function (e, cf, cg, ch, ci, cj, ck, cl, cm) {
            var cn = new Object;
            cn.name = null;
            cn.index = 0;
            cn.workbook = null;
            cn.url = null;
            cn.isHidden = false;
            cn.sheetType = null;
            cn.zoneId = 0;
            cn.size = null;
            cn.isActive = false;
            cn.name = e;
            cn.sheetType = cf;
            cn.index = cg;
            cn.size = ch;
            cn.workbook = ci;
            cn.url = cj;
            cn.isActive = ck;
            cn.isHidden = cl;
            cn.zoneId = cm;
            return cn
        };
        global.tab._SheetInfoImpl = F;
        var G = function (e, cf, cg, ch, ci) {
            this.$g = null;
            this.$h = null;
            this.$i = null;
            this.$j = null;
            this.$2$1 = null;
            E.call(this, e, cf, cg);
            B.verifyValue(ch, 'storyPm');
            B.verifyValue(ci, 'findSheetFunc');
            this.$h = ci;
            this.update(ch)
        };
        G.__typeName = 'tab._StoryImpl';
        global.tab._StoryImpl = G;
        var H = function (e, cf) {
            this.$1 = null;
            this.$3 = 0;
            this.$4 = false;
            this.$5 = false;
            this.$2 = null;
            this.$6 = null;
            this.$7 = null;
            this.$8 = 0;
            this.$4 = e.isActive;
            this.$5 = e.isUpdated;
            this.$1 = e.caption;
            this.$3 = e.index;
            this.$6 = e.parentStoryImpl;
            this.$8 = e.storyPointId;
            this.$2 = cf;
            if (ss.isValue(cf)) {
                this.$2.set_parentStoryPointImpl(this);
                if (cf.get_sheetType() === 'dashboard') {
                    var cg = this.$2;
                    for (var ch = 0; ch < cg.get_worksheets().get__length(); ch++) {
                        var ci = cg.get_worksheets().get_item(ch);
                        ci._impl.set_parentStoryPointImpl(this)
                    }
                }
            }
        };
        H.__typeName = 'tab._StoryPointImpl';
        H.createContainedSheet = function (e, cf, cg, ch) {
            var ci = S.convertSheetType(e.sheetType);
            var cj = -1;
            var ck = bw.createAutomatic();
            var cl = false;
            var cm = ch(e.name);
            var cn = ss.isNullOrUndefined(cm);
            var co = (cn ? '' : cm.getUrl());
            var cp = F.$ctor(e.name, ci, cj, ck, cf.get_workbook(), co, cl, cn, e.zoneId);
            if (e.sheetType === 'worksheet') {
                var cq = null;
                var cr = new O(cp, cf, cg, cq);
                return cr
            } else if (e.sheetType === 'dashboard') {
                var cs = new w(cp, cf, cg);
                var ct = N.$0(e.dashboardZones);
                cs.$c(ct, ch);
                return cs
            } else if (e.sheetType === 'story') {
                throw J.createInternalError('Cannot have a story embedded within another story.')
            } else {
                throw J.createInternalError("Unknown sheet type '" + e.sheetType + "'")
            }
        };
        global.tab._StoryPointImpl = H;
        var I = function () {
        };
        I.__typeName = 'tab._StoryPointInfoImpl';
        I.$ctor = function (e, cf, cg, ch, ci, cj) {
            var ck = new Object;
            ck.storyPointId = 0;
            ck.parentStoryImpl = null;
            ck.caption = null;
            ck.index = 0;
            ck.isActive = false;
            ck.isUpdated = false;
            ck.caption = e;
            ck.index = cf;
            ck.storyPointId = cg;
            ck.isActive = ch;
            ck.isUpdated = ci;
            ck.parentStoryImpl = cj;
            return ck
        };
        global.tab._StoryPointInfoImpl = I;
        var J = function () {
        };
        J.__typeName = 'tab._TableauException';
        J.create = function (e, cf) {
            var cg = new ss.Exception(cf);
            cg['tableauSoftwareErrorCode'] = e;
            return cg
        };
        J.createInternalError = function (e) {
            if (ss.isValue(e)) {
                return J.create('internalError', 'Internal error. Please contact Tableau support with the following information: ' + e)
            } else {
                return J.create('internalError', 'Internal error. Please contact Tableau support')
            }
        };
        J.createInternalNullArgumentException = function (e) {
            return J.createInternalError("Null/undefined argument '" + e + "'.")
        };
        J.createInternalStringArgumentException = function (e) {
            return J.createInternalError("Invalid string argument '" + e + "'.")
        };
        J.createServerError = function (e) {
            return J.create('serverError', e)
        };
        J.createNotActiveSheet = function () {
            return J.create('notActiveSheet', 'Operation not allowed on non-active sheet')
        };
        J.createInvalidCustomViewName = function (e) {
            return J.create('invalidCustomViewName', 'Invalid custom view name: ' + e)
        };
        J.createInvalidParameter = function (e) {
            return J.create('invalidParameter', 'Invalid parameter: ' + e)
        };
        J.createInvalidFilterFieldNameOrValue = function (e) {
            return J.create('invalidFilterFieldNameOrValue', 'Invalid filter field name or value: ' + e)
        };
        J.createInvalidDateParameter = function (e) {
            return J.create('invalidDateParameter', 'Invalid date parameter: ' + e)
        };
        J.createNullOrEmptyParameter = function (e) {
            return J.create('nullOrEmptyParameter', 'Parameter cannot be null or empty: ' + e)
        };
        J.createMissingMaxSize = function () {
            return J.create('missingMaxSize', 'Missing maxSize for SheetSizeBehavior.ATMOST')
        };
        J.createMissingMinSize = function () {
            return J.create('missingMinSize', 'Missing minSize for SheetSizeBehavior.ATLEAST')
        };
        J.createMissingMinMaxSize = function () {
            return J.create('missingMinMaxSize', 'Missing minSize or maxSize for SheetSizeBehavior.RANGE')
        };
        J.createInvalidRangeSize = function () {
            return J.create('invalidSize', 'Missing minSize or maxSize for SheetSizeBehavior.RANGE')
        };
        J.createInvalidSizeValue = function () {
            return J.create('invalidSize', 'Size value cannot be less than zero')
        };
        J.createInvalidSheetSizeParam = function () {
            return J.create('invalidSize', 'Invalid sheet size parameter')
        };
        J.createSizeConflictForExactly = function () {
            return J.create('invalidSize', 'Conflicting size values for SheetSizeBehavior.EXACTLY')
        };
        J.createInvalidSizeBehaviorOnWorksheet = function () {
            return J.create('invalidSizeBehaviorOnWorksheet', 'Only SheetSizeBehavior.AUTOMATIC is allowed on Worksheets')
        };
        J.createNoUrlForHiddenWorksheet = function () {
            return J.create('noUrlForHiddenWorksheet', 'Hidden worksheets do not have a URL.')
        };
        J.$0 = function (e) {
            return J.create('invalidAggregationFieldName', "Invalid aggregation type for field '" + e + "'")
        };
        J.createIndexOutOfRange = function (e) {
            return J.create('indexOutOfRange', "Index '" + e + "' is out of range.")
        };
        J.createUnsupportedEventName = function (e) {
            return J.create('unsupportedEventName', "Unsupported event '" + e + "'.")
        };
        J.createBrowserNotCapable = function () {
            return J.create('browserNotCapable', 'This browser is incapable of supporting the Tableau JavaScript API.')
        };
        global.tab._TableauException = J;
        var K = function () {
        };
        K.__typeName = 'tab._Utility';
        K.isNullOrEmpty = function (e) {
            return ss.isNullOrUndefined(e) || (e['length'] || 0) <= 0
        };
        K.isString = function (e) {
            return typeof(e) === 'string'
        };
        K.isNumber = function (e) {
            return typeof(e) === 'number'
        };
        K.isDate = function (e) {
            if (typeof(e) === 'object' && ss.isInstanceOfType(e, ss.JsDate)) {
                return true
            } else if (Object.prototype.toString.call(e) !== '[object Date]') {
                return false
            }
            return !isNaN(e.getTime())
        };
        K.isDateValid = function (e) {
            return !isNaN(e.getTime())
        };
        K.indexOf = function (e, cf, cg) {
            if (ss.isValue(Array.prototype['indexOf'])) {
                return e['indexOf'](cf, cg)
            }
            cg = cg || 0;
            var ch = e.length;
            if (ch > 0) {
                for (var ci = cg; ci < ch; ci++) {
                    if (ss.referenceEquals(e[ci], cf)) {
                        return ci
                    }
                }
            }
            return -1
        };
        K.contains = function (e, cf, cg) {
            var ch = K.indexOf(e, cf, cg);
            return ch >= 0
        };
        K.getTopmostWindow = function () {
            var e = window.self;
            while (ss.isValue(e.parent) && !ss.referenceEquals(e.parent, e)) {
                e = e.parent
            }
            return e
        };
        K.toInt = function (e) {
            if (K.isNumber(e)) {
                return ss.Int32.trunc(e)
            }
            var cf = parseInt(e.toString(), 10);
            if (isNaN(cf)) {
                return 0
            }
            return cf
        };
        K.hasClass = function (e, cf) {
            var cg = new RegExp('[\\n\\t\\r]', 'g');
            return ss.isValue(e) && (' ' + e.className + ' ').replace(cg, ' ').indexOf(' ' + cf + ' ') > -1
        };
        K.findParentWithClassName = function (e, cf, cg) {
            var ch = (ss.isValue(e) ? e.parentNode : null);
            cg = cg || document.body;
            while (ss.isValue(ch)) {
                if (K.hasClass(ch, cf)) {
                    return ch
                }
                if (ss.referenceEquals(ch, cg)) {
                    ch = null
                } else {
                    ch = ch.parentNode
                }
            }
            return ch
        };
        K.hasJsonParse = function () {
            return ss.isValue(JSON) && ss.isValue(JSON.parse)
        };
        K.hasWindowPostMessage = function () {
            return ss.isValue(window.postMessage)
        };
        K.isPostMessageSynchronous = function () {
            if (K.isIE()) {
                var e = new RegExp('(msie) ([\\w.]+)');
                var cf = e.exec(window.navigator.userAgent.toLowerCase());
                var cg = cf[2] || '0';
                var ch = parseInt(cg, 10);
                return ch <= 8
            }
            return false
        };
        K.hasDocumentAttachEvent = function () {
            return ss.isValue(document.attachEvent)
        };
        K.hasWindowAddEventListener = function () {
            return ss.isValue(window.addEventListener)
        };
        K.isElementOfTag = function (e, cf) {
            return ss.isValue(e) && e.nodeType === 1 && ss.referenceEquals(e.tagName.toLowerCase(), cf.toLowerCase())
        };
        K.elementToString = function (e) {
            var cf = new ss.StringBuilder;
            cf.append(e.tagName.toLowerCase());
            if (!K.isNullOrEmpty(e.id)) {
                cf.append('#').append(e.id)
            }
            if (!K.isNullOrEmpty(e.className)) {
                var cg = e.className.split(' ');
                cf.append('.').append(cg.join('.'))
            }
            return cf.toString()
        };
        K.tableauGCS = function (e) {
            if (typeof(window['getComputedStyle']) === 'function') {
                return window.getComputedStyle(e)
            } else {
                return e['currentStyle']
            }
        };
        K.isIE = function () {
            return window.navigator.userAgent.indexOf('MSIE') > -1 && ss.isNullOrUndefined(window.opera)
        };
        K.isSafari = function () {
            var e = window.navigator.userAgent;
            var cf = e.indexOf('Chrome') >= 0;
            return e.indexOf('Safari') >= 0 && !cf
        };
        K.mobileDetect = function () {
            var e = window.navigator.userAgent;
            if (e.indexOf('iPad') !== -1) {
                return true
            }
            if (e.indexOf('Android') !== -1) {
                return true
            }
            if (e.indexOf('AppleWebKit') !== -1 && e.indexOf('Mobile') !== -1) {
                return true
            }
            return false
        };
        K.visibleContentRectInDocumentCoordinates = function (e) {
            var cf = K.contentRectInDocumentCoordinates(e);
            for (var cg = e.parentElement; ss.isValue(cg) && ss.isValue(cg.parentElement); cg = cg.parentElement) {
                var ch = K.$0(cg).overflow;
                if (ch === 'auto' || ch === 'scroll' || ch === 'hidden') {
                    cf = cf.intersect(K.contentRectInDocumentCoordinates(cg))
                }
            }
            var ci = K.contentRectInDocumentCoordinates(document.documentElement);
            var cj = new tab.WindowHelper(window.self);
            if (cj.isQuirksMode()) {
                ci.height = document.body.clientHeight - ci.left;
                ci.width = document.body.clientWidth - ci.top
            }
            ci.left += cj.get_pageXOffset();
            ci.top += cj.get_pageYOffset();
            return cf.intersect(ci)
        };
        K.contentRectInDocumentCoordinates = function (e) {
            var cf = K.getBoundingClientRect(e);
            var cg = K.$0(e);
            var ch = K.toInt(cg.paddingLeft);
            var ci = K.toInt(cg.paddingTop);
            var cj = K.toInt(cg.borderLeftWidth);
            var ck = K.toInt(cg.borderTopWidth);
            var cl = K.computeContentSize(e);
            var cm = new tab.WindowHelper(window.self);
            var cn = cf.left + ch + cj + cm.get_pageXOffset();
            var co = cf.top + ci + ck + cm.get_pageYOffset();
            return new D(cn, co, cl.width, cl.height)
        };
        K.getBoundingClientRect = function (e) {
            var cf = e.getBoundingClientRect();
            var cg = ss.Int32.trunc(cf.top);
            var ch = ss.Int32.trunc(cf.left);
            var ci = ss.Int32.trunc(cf.right);
            var cj = ss.Int32.trunc(cf.bottom);
            return new D(ch, cg, ci - ch, cj - cg)
        };
        K.convertRawValue = function (e, cf) {
            if (ss.isNullOrUndefined(e)) {
                return null
            }
            switch (cf) {
                case'bool': {
                    return e
                }
                case'date':
                case'number': {
                    if (ss.isNullOrUndefined(e)) {
                        return Number.NaN
                    }
                    return e
                }
                default:
                case'string': {
                    return e
                }
            }
        };
        K.getDataValue = function (e) {
            if (ss.isNullOrUndefined(e)) {
                return bl.$ctor(null, null, null)
            }
            return bl.$ctor(K.convertRawValue(e.value, e.type), e.formattedValue, e.aliasedValue)
        };
        K.serializeDateForServer = function (e) {
            var cf = '';
            if (ss.isValue(e) && K.isDate(e)) {
                var cg = e.getUTCFullYear();
                var ch = e.getUTCMonth() + 1;
                var ci = e.getUTCDate();
                var cj = e.getUTCHours();
                var ck = e.getUTCMinutes();
                var cl = e.getUTCSeconds();
                cf = cg + '-' + ch + '-' + ci + ' ' + cj + ':' + ck + ':' + cl
            }
            return cf
        };
        K.computeContentSize = function (e) {
            var cf = K.$0(e);
            var cg = parseFloat(cf.paddingLeft);
            var ch = parseFloat(cf.paddingTop);
            var ci = parseFloat(cf.paddingRight);
            var cj = parseFloat(cf.paddingBottom);
            var ck = e.clientWidth - Math.round(cg + ci);
            var cl = e.clientHeight - Math.round(ch + cj);
            return bx.$ctor(ck, cl)
        };
        K.$0 = function (e) {
            if (typeof(window['getComputedStyle']) === 'function') {
                if (ss.isValue(e.ownerDocument.defaultView.opener)) {
                    return e.ownerDocument.defaultView.getComputedStyle(e)
                }
                return window.getComputedStyle(e)
            } else if (ss.isValue(e['currentStyle'])) {
                return e['currentStyle']
            }
            return e.style
        };
        K.roundVizSizeInPixels = function (e) {
            if (ss.isNullOrUndefined(e) || !(e.indexOf('px') !== -1)) {
                return e
            }
            var cf = parseFloat(e.split('px')[0]);
            return Math.round(cf) + 'px'
        };
        global.tab._Utility = K;
        var L = function () {
        };
        L.__typeName = 'tab._VizManagerImpl';
        L.$4 = function () {
            return L.$5.concat()
        };
        L.$0 = function (e) {
            L.$3(e);
            L.$5.push(e)
        };
        L.$2 = function (e) {
            for (var cf = 0, cg = L.$5.length; cf < cg; cf++) {
                if (ss.referenceEquals(L.$5[cf], e)) {
                    L.$5.splice(cf, 1);
                    break
                }
            }
        };
        L.$1 = function () {
            for (var e = 0, cf = L.$5.length; e < cf; e++) {
                L.$5[e]._impl.$M()
            }
        };
        L.$3 = function (e) {
            var cf = e.getParentElement();
            for (var cg = 0, ch = L.$5.length; cg < ch; cg++) {
                if (ss.referenceEquals(L.$5[cg].getParentElement(), cf)) {
                    var ci = "Another viz is already present in element '" + K.elementToString(cf) + "'.";
                    throw J.create('vizAlreadyInManager', ci)
                }
            }
        };
        var M = function (e, cf, cg) {
            this.name = '';
            this.host_url = null;
            this.tabs = false;
            this.toolbar = false;
            this.toolBarPosition = null;
            this.device = null;
            this.hostId = null;
            this.width = null;
            this.height = null;
            this.parentElement = null;
            this.userSuppliedParameters = null;
            this.staticImageUrl = null;
            this.fixedSize = false;
            this.displayStaticImage = false;
            this.$2 = null;
            this.$1 = null;
            if (ss.isNullOrUndefined(e) || ss.isNullOrUndefined(cf)) {
                throw J.create('noUrlOrParentElementNotFound', 'URL is empty or Parent element not found')
            }
            if (ss.isNullOrUndefined(cg)) {
                cg = new Object;
                cg.hideTabs = false;
                cg.hideToolbar = false;
                cg.onFirstInteractive = null
            }
            if (ss.isValue(cg.height) || ss.isValue(cg.width)) {
                this.fixedSize = true;
                if (K.isNumber(cg.height)) {
                    cg.height = cg.height.toString() + 'px'
                }
                if (K.isNumber(cg.width)) {
                    cg.width = cg.width.toString() + 'px'
                }
                this.height = (ss.isValue(cg.height) ? K.roundVizSizeInPixels(cg.height.toString()) : null);
                this.width = (ss.isValue(cg.width) ? K.roundVizSizeInPixels(cg.width.toString()) : null)
            } else {
                this.fixedSize = false
            }
            this.displayStaticImage = cg.displayStaticImage || false;
            this.staticImageUrl = cg.staticImageUrl || '';
            this.tabs = !(cg.hideTabs || false);
            this.toolbar = !(cg.hideToolbar || false);
            this.device = cg.device;
            this.parentElement = e;
            this.$1 = cg;
            this.toolBarPosition = cg.toolbarPosition;
            var ch = cf.split('?');
            this.$2 = ch[0];
            if (ch.length === 2) {
                this.userSuppliedParameters = ch[1]
            } else {
                this.userSuppliedParameters = ''
            }
            var ci = (new RegExp('.*?[^/:]/', '')).exec(this.$2);
            if (ss.isNullOrUndefined(ci) || ci[0].toLowerCase().indexOf('http://') === -1 && ci[0].toLowerCase().indexOf('https://') === -1) {
                throw J.create('invalidUrl', 'Invalid url')
            }
            this.host_url = ci[0].toLowerCase();
            this.name = this.$2.replace(ci[0], '');
            this.name = this.name.replace('views/', '')
        };
        M.__typeName = 'tab._VizParameters';
        global.tab._VizParameters = M;
        var N = function (e, cf, cg) {
            this.$E = null;
            this.$D = null;
            this.$y = null;
            this.$s = null;
            this.$r = null;
            this.$A = new tab._Collection;
            this.$v = false;
            this.$x = null;
            this.$t = null;
            this.$u = new tab._Collection;
            this.$C = new tab._Collection;
            this.$B = new tab._Collection;
            this.$z = null;
            this.$w = null;
            this.$D = e;
            this.$x = cf;
            this.$5(cg)
        };
        N.__typeName = 'tab._WorkbookImpl';
        N.$0 = function (e) {
            e = ss.coalesce(e, []);
            var cf = [];
            for (var cg = 0; cg < e.length; cg++) {
                var ch = e[cg];
                var ci = S.convertDashboardObjectType(ch.zoneType);
                var cj = bx.$ctor(ch.width, ch.height);
                var ck = bu.$ctor(ch.x, ch.y);
                var cl = ch.name;
                var cm = {name: cl, objectType: ci, position: ck, size: cj, zoneId: ch.zoneId};
                cf.push(cm)
            }
            return cf
        };
        N.$2 = function (e) {
            if (ss.isNullOrUndefined(e)) {
                return null
            }
            if (K.isString(e)) {
                return e
            }
            var cf = ss.safeCast(e, bV);
            if (ss.isValue(cf)) {
                return cf.getName()
            }
            var cg = ss.safeCast(e, bW);
            if (ss.isValue(cg)) {
                return cg.getName()
            }
            return null
        };
        N.$1 = function (e) {
            if (ss.isNullOrUndefined(e)) {
                return bw.createAutomatic()
            }
            return bw.fromSizeConstraints(e.sizeConstraints)
        };
        N.$4 = function (e) {
            var cf = new tab._Collection;
            for (var cg = 0; cg < e.parameters.length; cg++) {
                var ch = e.parameters[cg];
                var ci = new m(ch);
                cf._add(ci.$7(), ci.$8())
            }
            return cf
        };
        N.$3 = function (e, cf) {
            for (var cg = 0; cg < cf.parameters.length; cg++) {
                var ch = cf.parameters[cg];
                if (ss.referenceEquals(ch.name, e)) {
                    return new m(ch)
                }
            }
            return null
        };
        global.tab._WorkbookImpl = N;
        var O = function (e, cf, cg, ch) {
            this.$K = null;
            this.$I = null;
            this.$H = new tab._Collection;
            this.$J = new tab._Collection;
            this.highlightedMarks = null;
            E.call(this, e, cf, cg);
            this.$I = ch
        };
        O.__typeName = 'tab._WorksheetImpl';
        O.$2 = function (e) {
            var cf = e;
            if (ss.isValue(cf) && ss.isValue(cf.errorCode)) {
                var cg = (ss.isValue(cf.additionalInformation) ? cf.additionalInformation.toString() : '');
                switch (cf.errorCode) {
                    case'invalidFilterFieldName': {
                        return J.create('invalidFilterFieldName', cg)
                    }
                    case'invalidFilterFieldValue': {
                        return J.create('invalidFilterFieldValue', cg)
                    }
                    case'invalidAggregationFieldName': {
                        return J.$0(cg)
                    }
                    default: {
                        return J.createServerError(cg)
                    }
                }
            }
            return null
        };
        O.$3 = function (e) {
            if (ss.isNullOrUndefined(e)) {
                throw J.createNullOrEmptyParameter('filterOptions')
            }
            if (ss.isNullOrUndefined(e.min) && ss.isNullOrUndefined(e.max)) {
                throw J.create('invalidParameter', 'At least one of filterOptions.min or filterOptions.max must be specified.')
            }
            var cf = new Object;
            if (ss.isValue(e.min)) {
                cf.min = e.min
            }
            if (ss.isValue(e.max)) {
                cf.max = e.max
            }
            if (ss.isValue(e.nullOption)) {
                cf.nullOption = n.$1(Y).call(null, e.nullOption, 'filterOptions.nullOption')
            }
            return cf
        };
        O.$4 = function (e) {
            if (ss.isNullOrUndefined(e)) {
                throw J.createNullOrEmptyParameter('filterOptions')
            }
            var cf = new Object;
            cf.rangeType = n.$1(Q).call(null, e.rangeType, 'filterOptions.rangeType');
            cf.periodType = n.$1(bb).call(null, e.periodType, 'filterOptions.periodType');
            if (cf.rangeType === 'lastn' || cf.rangeType === 'nextn') {
                if (ss.isNullOrUndefined(e.rangeN)) {
                    throw J.create('missingRangeNForRelativeDateFilters', 'Missing rangeN field for a relative date filter of LASTN or NEXTN.')
                }
                cf.rangeN = K.toInt(e.rangeN)
            }
            if (ss.isValue(e.anchorDate)) {
                if (!K.isDate(e.anchorDate) || !K.isDateValid(e.anchorDate)) {
                    throw J.createInvalidDateParameter('filterOptions.anchorDate')
                }
                cf.anchorDate = e.anchorDate
            }
            return cf
        };
        O.$0 = function (e, cf, cg) {
            return new (ss.makeGenericType(bh, [Object]))(e, 1, function (ch) {
                var ci = O.$2(ch);
                if (ss.isNullOrUndefined(ci)) {
                    cg.resolve(cf)
                } else {
                    cg.reject(ci)
                }
            }, function (ch, ci) {
                if (ch) {
                    cg.reject(J.createInvalidFilterFieldNameOrValue(cf))
                } else {
                    var cj = J.create('filterCannotBePerformed', ci);
                    cg.reject(cj)
                }
            })
        };
        O.$1 = function (e) {
            var cf = e;
            if (ss.isValue(cf) && ss.isValue(cf.errorCode)) {
                var cg = (ss.isValue(cf.additionalInformation) ? cf.additionalInformation.toString() : '');
                switch (cf.errorCode) {
                    case'invalidSelectionFieldName': {
                        return J.create('invalidSelectionFieldName', cg)
                    }
                    case'invalidSelectionValue': {
                        return J.create('invalidSelectionValue', cg)
                    }
                    case'invalidSelectionDate': {
                        return J.create('invalidSelectionDate', cg)
                    }
                }
            }
            return null
        };
        global.tab._WorksheetImpl = O;
        var P = function () {
        };
        P.__typeName = 'tab.ApiDashboardObjectType';
        global.tab.ApiDashboardObjectType = P;
        var Q = function () {
        };
        Q.__typeName = 'tab.ApiDateRangeType';
        global.tab.ApiDateRangeType = Q;
        var R = function () {
        };
        R.__typeName = 'tab.ApiDeviceType';
        global.tab.ApiDeviceType = R;
        var S = function () {
        };
        S.__typeName = 'tab.ApiEnumConverter';
        S.convertDashboardObjectType = function (e) {
            switch (e) {
                case'blank': {
                    return 'blank'
                }
                case'image': {
                    return 'image'
                }
                case'legend': {
                    return 'legend'
                }
                case'pageFilter': {
                    return 'pageFilter'
                }
                case'parameterControl': {
                    return 'parameterControl'
                }
                case'quickFilter': {
                    return 'quickFilter'
                }
                case'text': {
                    return 'text'
                }
                case'title': {
                    return 'title'
                }
                case'webPage': {
                    return 'webPage'
                }
                case'worksheet': {
                    return 'worksheet'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainDashboardObjectType: ' + e)
                }
            }
        };
        S.convertDateRange = function (e) {
            switch (e) {
                case'curr': {
                    return 'curr'
                }
                case'last': {
                    return 'last'
                }
                case'lastn': {
                    return 'lastn'
                }
                case'next': {
                    return 'next'
                }
                case'nextn': {
                    return 'nextn'
                }
                case'todate': {
                    return 'todate'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainDateRangeType: ' + e)
                }
            }
        };
        S.convertFieldAggregation = function (e) {
            switch (e) {
                case'ATTR': {
                    return 'ATTR'
                }
                case'AVG': {
                    return 'AVG'
                }
                case'COUNT': {
                    return 'COUNT'
                }
                case'COUNTD': {
                    return 'COUNTD'
                }
                case'DAY': {
                    return 'DAY'
                }
                case'END': {
                    return 'END'
                }
                case'HOUR': {
                    return 'HOUR'
                }
                case'INOUT': {
                    return 'INOUT'
                }
                case'KURTOSIS': {
                    return 'KURTOSIS'
                }
                case'MAX': {
                    return 'MAX'
                }
                case'MDY': {
                    return 'MDY'
                }
                case'MEDIAN': {
                    return 'MEDIAN'
                }
                case'MIN': {
                    return 'MIN'
                }
                case'MINUTE': {
                    return 'MINUTE'
                }
                case'MONTH': {
                    return 'MONTH'
                }
                case'MONTHYEAR': {
                    return 'MONTHYEAR'
                }
                case'NONE': {
                    return 'NONE'
                }
                case'PERCENTILE': {
                    return 'PERCENTILE'
                }
                case'QUART1': {
                    return 'QUART1'
                }
                case'QUART3': {
                    return 'QUART3'
                }
                case'QTR': {
                    return 'QTR'
                }
                case'SECOND': {
                    return 'SECOND'
                }
                case'SKEWNESS': {
                    return 'SKEWNESS'
                }
                case'STDEV': {
                    return 'STDEV'
                }
                case'STDEVP': {
                    return 'STDEVP'
                }
                case'SUM': {
                    return 'SUM'
                }
                case'SUM_XSQR': {
                    return 'SUM_XSQR'
                }
                case'TRUNC_DAY': {
                    return 'TRUNC_DAY'
                }
                case'TRUNC_HOUR': {
                    return 'TRUNC_HOUR'
                }
                case'TRUNC_MINUTE': {
                    return 'TRUNC_MINUTE'
                }
                case'TRUNC_MONTH': {
                    return 'TRUNC_MONTH'
                }
                case'TRUNC_QTR': {
                    return 'TRUNC_QTR'
                }
                case'TRUNC_SECOND': {
                    return 'TRUNC_SECOND'
                }
                case'TRUNC_WEEK': {
                    return 'TRUNC_WEEK'
                }
                case'TRUNC_YEAR': {
                    return 'TRUNC_YEAR'
                }
                case'USER': {
                    return 'USER'
                }
                case'VAR': {
                    return 'VAR'
                }
                case'VARP': {
                    return 'VARP'
                }
                case'WEEK': {
                    return 'WEEK'
                }
                case'WEEKDAY': {
                    return 'WEEKDAY'
                }
                case'YEAR': {
                    return 'YEAR'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainFieldAggregationType: ' + e)
                }
            }
        };
        S.convertFieldRole = function (e) {
            switch (e) {
                case'dimension': {
                    return 'dimension'
                }
                case'measure': {
                    return 'measure'
                }
                case'unknown': {
                    return 'unknown'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainFieldRoleType: ' + e)
                }
            }
        };
        S.convertFilterType = function (e) {
            switch (e) {
                case'categorical': {
                    return 'categorical'
                }
                case'hierarchical': {
                    return 'hierarchical'
                }
                case'quantitative': {
                    return 'quantitative'
                }
                case'relativedate': {
                    return 'relativedate'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainFilterType: ' + e)
                }
            }
        };
        S.convertParameterAllowableValuesType = function (e) {
            switch (e) {
                case'all': {
                    return 'all'
                }
                case'list': {
                    return 'list'
                }
                case'range': {
                    return 'range'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainParameterAllowableValuesType: ' + e)
                }
            }
        };
        S.convertParameterDataType = function (e) {
            switch (e) {
                case'boolean': {
                    return 'boolean'
                }
                case'date': {
                    return 'date'
                }
                case'datetime': {
                    return 'datetime'
                }
                case'float': {
                    return 'float'
                }
                case'integer': {
                    return 'integer'
                }
                case'string': {
                    return 'string'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainParameterDataType: ' + e)
                }
            }
        };
        S.convertPeriodType = function (e) {
            switch (e) {
                case'year': {
                    return 'year'
                }
                case'quarter': {
                    return 'quarter'
                }
                case'month': {
                    return 'month'
                }
                case'week': {
                    return 'week'
                }
                case'day': {
                    return 'day'
                }
                case'hour': {
                    return 'hour'
                }
                case'minute': {
                    return 'minute'
                }
                case'second': {
                    return 'second'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainPeriodType: ' + e)
                }
            }
        };
        S.convertSheetType = function (e) {
            switch (e) {
                case'worksheet': {
                    return 'worksheet'
                }
                case'dashboard': {
                    return 'dashboard'
                }
                case'story': {
                    return 'story'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainSheetType: ' + e)
                }
            }
        };
        S.convertDataType = function (e) {
            switch (e) {
                case'boolean': {
                    return 'boolean'
                }
                case'date': {
                    return 'date'
                }
                case'datetime': {
                    return 'datetime'
                }
                case'float': {
                    return 'float'
                }
                case'integer': {
                    return 'integer'
                }
                case'string': {
                    return 'string'
                }
                default: {
                    throw J.createInternalError('Unknown ApiCrossDomainParameterDataType: ' + e)
                }
            }
        };
        global.tab.ApiEnumConverter = S;
        var T = function () {
        };
        T.__typeName = 'tab.ApiErrorCode';
        global.tab.ApiErrorCode = T;
        var U = function () {
        };
        U.__typeName = 'tab.ApiFieldAggregationType';
        global.tab.ApiFieldAggregationType = U;
        var V = function () {
        };
        V.__typeName = 'tab.ApiFieldRoleType';
        global.tab.ApiFieldRoleType = V;
        var W = function () {
        };
        W.__typeName = 'tab.ApiFilterType';
        global.tab.ApiFilterType = W;
        var X = function () {
        };
        X.__typeName = 'tab.ApiFilterUpdateType';
        global.tab.ApiFilterUpdateType = X;
        var Y = function () {
        };
        Y.__typeName = 'tab.ApiNullOption';
        global.tab.ApiNullOption = Y;
        var Z = function () {
        };
        Z.__typeName = 'tab.ApiParameterAllowableValuesType';
        global.tab.ApiParameterAllowableValuesType = Z;
        var ba = function () {
        };
        ba.__typeName = 'tab.ApiParameterDataType';
        global.tab.ApiParameterDataType = ba;
        var bb = function () {
        };
        bb.__typeName = 'tab.ApiPeriodType';
        global.tab.ApiPeriodType = bb;
        var bc = function () {
        };
        bc.__typeName = 'tab.ApiSelectionUpdateType';
        global.tab.ApiSelectionUpdateType = bc;
        var bd = function () {
        };
        bd.__typeName = 'tab.ApiSheetSizeBehavior';
        global.tab.ApiSheetSizeBehavior = bd;
        var be = function () {
        };
        be.__typeName = 'tab.ApiSheetType';
        global.tab.ApiSheetType = be;
        var bf = function () {
        };
        bf.__typeName = 'tab.ApiTableauEventName';
        global.tab.ApiTableauEventName = bf;
        var bg = function () {
        };
        bg.__typeName = 'tab.ApiToolbarPosition';
        global.tab.ApiToolbarPosition = bg;
        var bh = function (e) {
            var cf = function (cg, ch, ci, cj) {
                this.$0 = null;
                this.$3 = 0;
                this.$2 = null;
                this.$1 = null;
                this.$0 = cg;
                this.$2 = ci;
                this.$3 = ch;
                this.$1 = cj
            };
            ss.registerGenericClassInstance(cf, bh, [e], {
                get_commandName: function () {
                    return this.$0
                }, get_successCallback: function () {
                    return this.$2
                }, get_successCallbackTiming: function () {
                    return this.$3
                }, get_errorCallback: function () {
                    return this.$1
                }
            }, function () {
                return null
            }, function () {
                return []
            });
            return cf
        };
        bh.__typeName = 'tab.CommandReturnHandler$1';
        ss.initGenericClass(bh, a, 1);
        global.tab.CommandReturnHandler$1 = bh;
        var bi = function (e, cf) {
            this.$1 = null;
            this.$0 = null;
            B.verifyValue(e, 'router');
            B.verifyValue(cf, 'handler');
            this.$1 = e;
            this.$0 = cf
        };
        bi.__typeName = 'tab.CrossDomainMessagingOptions';
        global.tab.CrossDomainMessagingOptions = bi;
        var bj = function (e, cf, cg) {
            this.$2 = null;
            bA.call(this, e, cf);
            this.$2 = new g(cf._impl.get__workbookImpl(), cg)
        };
        bj.__typeName = 'tab.CustomViewEvent';
        global.tab.CustomViewEvent = bj;
        var bk = function () {
        };
        bk.__typeName = 'tab.DataType';
        global.tab.DataType = bk;
        var bl = function () {
        };
        bl.__typeName = 'tab.DataValue';
        bl.$ctor = function (e, cf, cg) {
            var ch = new Object;
            ch.value = null;
            ch.formattedValue = null;
            ch.value = e;
            if (K.isNullOrEmpty(cg)) {
                ch.formattedValue = cf
            } else {
                ch.formattedValue = cg
            }
            return ch
        };
        global.tab.DataValue = bl;
        var bm = function (e, cf) {
            this.$0 = null;
            this.$1 = null;
            this.$0 = e;
            this.$1 = cf
        };
        bm.__typeName = 'tab.EventContext';
        global.tab.EventContext = bm;
        var bn = function (e, cf, cg, ch, ci) {
            this.$4 = null;
            this.$3 = null;
            bF.call(this, e, cf, cg);
            this.$4 = ci;
            this.$3 = new h(cf._impl.get__workbookImpl(), cg, ch, ci)
        };
        bn.__typeName = 'tab.FilterEvent';
        global.tab.FilterEvent = bn;
        var bo = function (e, cf, cg) {
            this.$2 = null;
            bA.call(this, e, cf);
            this.$2 = cg
        };
        bo.__typeName = 'tab.FirstVizSizeKnownEvent';
        global.tab.FirstVizSizeKnownEvent = bo;
        var bp = function (e, cf, cg) {
            this.$3 = null;
            bF.call(this, e, cf, cg);
            this.$3 = new i(cf._impl.get__workbookImpl(), cg)
        };
        bp.__typeName = 'tab.HighlightEvent';
        global.tab.HighlightEvent = bp;
        var bq = function () {
        };
        bq.__typeName = 'tab.ICrossDomainMessageHandler';
        global.tab.ICrossDomainMessageHandler = bq;
        var br = function () {
        };
        br.__typeName = 'tab.ICrossDomainMessageRouter';
        global.tab.ICrossDomainMessageRouter = br;
        var bs = function (e, cf, cg) {
            this.$3 = null;
            bF.call(this, e, cf, cg);
            this.$3 = new d(cf._impl.get__workbookImpl(), cg)
        };
        bs.__typeName = 'tab.MarksEvent';
        global.tab.MarksEvent = bs;
        var bt = function (e, cf, cg) {
            this.$2 = null;
            bA.call(this, e, cf);
            this.$2 = new f(cf._impl.get__workbookImpl(), cg)
        };
        bt.__typeName = 'tab.ParameterEvent';
        global.tab.ParameterEvent = bt;
        var bu = function () {
        };
        bu.__typeName = 'tab.Point';
        bu.$ctor = function (e, cf) {
            var cg = new Object;
            cg.x = 0;
            cg.y = 0;
            cg.x = e;
            cg.y = cf;
            return cg
        };
        global.tab.Point = bu;
        var bv = function () {
        };
        bv.__typeName = 'tab.SheetSize';
        bv.$ctor = function (e, cf, cg) {
            var ch = new Object;
            ch.behavior = null;
            ch.minSize = null;
            ch.maxSize = null;
            ch.behavior = ss.coalesce(e, 'automatic');
            if (ss.isValue(cf)) {
                ch.minSize = cf
            } else {
                delete ch['minSize']
            }
            if (ss.isValue(cg)) {
                ch.maxSize = cg
            } else {
                delete ch['maxSize']
            }
            return ch
        };
        global.tab.SheetSize = bv;
        var bw = function () {
        };
        bw.__typeName = 'tab.SheetSizeFactory';
        bw.createAutomatic = function () {
            var e = bv.$ctor('automatic', null, null);
            return e
        };
        bw.fromSizeConstraints = function (e) {
            var cf = e.minHeight;
            var cg = e.minWidth;
            var ch = e.maxHeight;
            var ci = e.maxWidth;
            var cj = 'automatic';
            var ck = null;
            var cl = null;
            if (cf === 0 && cg === 0) {
                if (ch === 0 && ci === 0) {
                } else {
                    cj = 'atmost';
                    cl = bx.$ctor(ci, ch)
                }
            } else if (ch === 0 && ci === 0) {
                cj = 'atleast';
                ck = bx.$ctor(cg, cf)
            } else if (ch === cf && ci === cg && cg > 0) {
                cj = 'exactly';
                ck = bx.$ctor(cg, cf);
                cl = bx.$ctor(cg, cf)
            } else {
                cj = 'range';
                if (cg === 0 && ci === 0) {
                    ci = 2147483647
                }
                ck = bx.$ctor(cg, cf);
                cl = bx.$ctor(ci, ch)
            }
            return bv.$ctor(cj, ck, cl)
        };
        global.tab.SheetSizeFactory = bw;
        var bx = function () {
        };
        bx.__typeName = 'tab.Size';
        bx.$ctor = function (e, cf) {
            var cg = new Object;
            cg.width = 0;
            cg.height = 0;
            cg.width = e;
            cg.height = cf;
            return cg
        };
        global.tab.Size = bx;
        var by = function () {
        };
        by.__typeName = 'tab.StoryPointInfoImplUtil';
        by.clone = function (e) {
            return I.$ctor(e.caption, e.index, e.storyPointId, e.isActive, e.isUpdated, e.parentStoryImpl)
        };
        global.tab.StoryPointInfoImplUtil = by;
        var bz = function (e, cf, cg, ch) {
            this.$3 = null;
            this.$2 = null;
            bA.call(this, e, cf);
            this.$3 = cg;
            this.$2 = ch
        };
        bz.__typeName = 'tab.StoryPointSwitchEvent';
        global.tab.StoryPointSwitchEvent = bz;
        var bA = function (e, cf) {
            this.$1 = null;
            this.$0 = null;
            this.$1 = cf;
            this.$0 = e
        };
        bA.__typeName = 'tab.TableauEvent';
        global.tab.TableauEvent = bA;
        var bB = function (e, cf, cg, ch) {
            this.$3 = null;
            this.$2 = null;
            bA.call(this, e, cf);
            this.$3 = cg;
            this.$2 = ch
        };
        bB.__typeName = 'tab.TabSwitchEvent';
        global.tab.TabSwitchEvent = bB;
        var bC = function (e, cf, cg, ch, ci) {
            this.$18 = null;
            this.$1m = null;
            this.$1b = null;
            this.$1l = null;
            this.$1k = null;
            this.$1c = null;
            this.$1e = null;
            this.$1p = null;
            this.$1i = null;
            this.$1j = null;
            this.$1h = false;
            this.$1a = false;
            this.$1f = false;
            this.$19 = false;
            this.$1g = null;
            this.$1n = null;
            this.$1o = null;
            this.$1d = false;
            this.$1$1 = null;
            this.$1$2 = null;
            this.$1$3 = null;
            this.$1$4 = null;
            this.$1$5 = null;
            this.$1$6 = null;
            this.$1$7 = null;
            this.$1$8 = null;
            this.$1$9 = null;
            this.$1$10 = null;
            this.$1$11 = null;
            this.$1$12 = null;
            this.$1$13 = null;
            if (!K.hasWindowPostMessage() || !K.hasJsonParse()) {
                throw J.createBrowserNotCapable()
            }
            this.$1g = new bi(e, this);
            this.$1m = cf;
            if (ss.isNullOrUndefined(cg) || cg.nodeType !== 1) {
                cg = document.body
            }
            this.$1k = new M(cg, ch, ci);
            if (ss.isValue(ci)) {
                this.$1i = ci.onFirstInteractive;
                this.$1j = ci.onFirstVizSizeKnown
            }
        };
        bC.__typeName = 'tab.VizImpl';
        global.tab.VizImpl = bC;
        var bD = function (e, cf, cg) {
            this.$2 = null;
            bA.call(this, e, cf);
            this.$2 = cg
        };
        bD.__typeName = 'tab.VizResizeEvent';
        global.tab.VizResizeEvent = bD;
        var bE = function () {
        };
        bE.__typeName = 'tab.VizSize';
        bE.$ctor = function (e, cf) {
            var cg = new Object;
            cg.sheetSize = null;
            cg.chromeHeight = 0;
            cg.sheetSize = e;
            cg.chromeHeight = cf;
            return cg
        };
        global.tab.VizSize = bE;
        var bF = function (e, cf, cg) {
            this.$2 = null;
            bA.call(this, e, cf);
            this.$2 = cg
        };
        bF.__typeName = 'tab.WorksheetEvent';
        global.tab.WorksheetEvent = bF;
        var bG = function (e, cf) {
            this.$a = false;
            this.$9 = null;
            bO.call(this, e, cf);
            this.$8(cf)
        };
        bG.__typeName = 'tableauSoftware.CategoricalFilter';
        global.tableauSoftware.CategoricalFilter = bG;
        var bH = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        bH.__typeName = 'tableauSoftware.Column';
        global.tableauSoftware.Column = bH;
        var bI = function (e) {
            this._impl = null;
            this._impl = e
        };
        bI.__typeName = 'tableauSoftware.CustomView';
        global.tableauSoftware.CustomView = bI;
        var bJ = function (e) {
            this._impl = null;
            bV.call(this, e)
        };
        bJ.__typeName = 'tableauSoftware.Dashboard';
        global.tableauSoftware.Dashboard = bJ;
        var bK = function (e, cf, cg) {
            this.$2 = null;
            this.$0 = null;
            this.$1 = null;
            if (e.objectType === 'worksheet' && ss.isNullOrUndefined(cg)) {
                throw J.createInternalError('worksheet parameter is required for WORKSHEET objects')
            } else if (e.objectType !== 'worksheet' && ss.isValue(cg)) {
                throw J.createInternalError('worksheet parameter should be undefined for non-WORKSHEET objects')
            }
            this.$2 = e;
            this.$0 = cf;
            this.$1 = cg
        };
        bK.__typeName = 'tableauSoftware.DashboardObject';
        global.tableauSoftware.DashboardObject = bK;
        var bL = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        bL.__typeName = 'tableauSoftware.DataSource';
        global.tableauSoftware.DataSource = bL;
        var bM = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        bM.__typeName = 'tableauSoftware.DataTable';
        global.tableauSoftware.DataTable = bM;
        var bN = function (e, cf, cg, ch) {
            this.$0 = null;
            this.$3 = null;
            this.$2 = null;
            this.$1 = null;
            this.$0 = e;
            this.$3 = cf;
            this.$2 = cg;
            this.$1 = ch
        };
        bN.__typeName = 'tableauSoftware.Field';
        global.tableauSoftware.Field = bN;
        var bO = function (e, cf) {
            this.$7 = null;
            this.$6 = null;
            this.$1 = null;
            this.$3 = null;
            this.$2 = null;
            this.$5 = null;
            this.$4 = null;
            this.$7 = e;
            this.$0(cf)
        };
        bO.__typeName = 'tableauSoftware.Filter';
        bO.$0 = function (e, cf) {
            switch (cf.filterType) {
                case'categorical': {
                    return new bG(e, cf)
                }
                case'relativedate': {
                    return new bU(e, cf)
                }
                case'hierarchical': {
                    return new bP(e, cf)
                }
                case'quantitative': {
                    return new bT(e, cf)
                }
            }
            return null
        };
        bO.processFiltersList = function (e, cf) {
            var cg = new tab._Collection;
            for (var ch = 0; ch < cf.filters.length; ch++) {
                var ci = cf.filters[ch];
                if (!cg._has(ci.caption)) {
                    cg._add(ci.caption, ci.caption)
                }
            }
            var cj = new tab._Collection;
            for (var ck = 0; ck < cf.filters.length; ck++) {
                var cl = cf.filters[ck];
                var cm = bO.$0(e, cl);
                if (!cj._has(cl.caption)) {
                    cj._add(cl.caption, cm);
                    continue
                }
                var cn = cl.caption.toString() + '_' + cl.filterType.toString();
                var co = cn;
                var cp = 1;
                while (cg._has(co)) {
                    co = cn + '_' + cp;
                    cp++
                }
                cj._add(co, cm)
            }
            return cj
        };
        global.tableauSoftware.Filter = bO;
        var bP = function (e, cf) {
            this.$9 = 0;
            bO.call(this, e, cf);
            this.$8(cf)
        };
        bP.__typeName = 'tableauSoftware.HierarchicalFilter';
        global.tableauSoftware.HierarchicalFilter = bP;
        var bQ = function (e) {
            this.$0 = null;
            this.$0 = new l(e)
        };
        bQ.__typeName = 'tableauSoftware.Mark';
        global.tableauSoftware.Mark = bQ;
        var bR = function (e, cf) {
            this.fieldName = null;
            this.value = null;
            this.formattedValue = null;
            this.fieldName = e;
            this.value = cf;
            this.formattedValue = (ss.isValue(cf) ? cf.toString() : '')
        };
        bR.__typeName = 'tableauSoftware.Pair';
        global.tableauSoftware.Pair = bR;
        var bS = function (e) {
            this._impl = null;
            this._impl = e
        };
        bS.__typeName = 'tableauSoftware.Parameter';
        global.tableauSoftware.Parameter = bS;
        var bT = function (e, cf) {
            this.$a = null;
            this.$9 = null;
            this.$d = null;
            this.$c = null;
            this.$b = false;
            bO.call(this, e, cf);
            this.$8(cf)
        };
        bT.__typeName = 'tableauSoftware.QuantitativeFilter';
        global.tableauSoftware.QuantitativeFilter = bT;
        var bU = function (e, cf) {
            this.$9 = null;
            this.$b = null;
            this.$a = 0;
            bO.call(this, e, cf);
            this.$8(cf)
        };
        bU.__typeName = 'tableauSoftware.RelativeDateFilter';
        global.tableauSoftware.RelativeDateFilter = bU;
        var bV = function (e) {
            this._impl = null;
            B.verifyValue(e, 'sheetImpl');
            this._impl = e
        };
        bV.__typeName = 'tableauSoftware.Sheet';
        global.tableauSoftware.Sheet = bV;
        var bW = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        bW.__typeName = 'tableauSoftware.SheetInfo';
        global.tableauSoftware.SheetInfo = bW;
        var bX = function (e) {
            this._impl = null;
            bV.call(this, e)
        };
        bX.__typeName = 'tableauSoftware.Story';
        global.tableauSoftware.Story = bX;
        var bY = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        bY.__typeName = 'tableauSoftware.StoryPoint';
        global.tableauSoftware.StoryPoint = bY;
        var bZ = function (e) {
            this._impl = null;
            this._impl = e
        };
        bZ.__typeName = 'tableauSoftware.StoryPointInfo';
        global.tableauSoftware.StoryPointInfo = bZ;
        var ca = function (e, cf, cg, ch) {
            this.$0 = 0;
            this.$2 = 0;
            this.$3 = 0;
            this.$1 = null;
            this.$0 = e;
            this.$2 = cf;
            this.$3 = cg;
            this.$1 = ss.coalesce(ch, null)
        };
        ca.__typeName = 'tableauSoftware.Version';
        ca.getCurrent = function () {
            return ca.$0
        };
        global.tableauSoftware.Version = ca;
        var cb = function (e, cf, cg) {
            this._impl = null;
            var ch = q.getCrossDomainMessageRouter();
            this._impl = new bC(ch, this, e, cf, cg);
            this._impl.$4()
        };
        cb.__typeName = 'tableauSoftware.Viz';
        global.tableauSoftware.Viz = cb;
        var cc = function () {
        };
        cc.__typeName = 'tableauSoftware.VizManager';
        cc.getVizs = function () {
            return L.$4()
        };
        global.tableauSoftware.VizManager = cc;
        var cd = function (e) {
            this.$0 = null;
            this.$0 = e
        };
        cd.__typeName = 'tableauSoftware.Workbook';
        global.tableauSoftware.Workbook = cd;
        var ce = function (e) {
            this._impl = null;
            bV.call(this, e)
        };
        ce.__typeName = 'tableauSoftware.Worksheet';
        global.tableauSoftware.Worksheet = ce;
        ss.initInterface(br, a, {registerHandler: null, unregisterHandler: null, sendCommand: null});
        ss.initClass(b, a, {
            registerHandler: function (e) {
                var cf = 'host' + this.$a;
                if (ss.isValue(e.get_hostId()) || ss.isValue(this.$9[e.get_hostId()])) {
                    throw J.createInternalError("Host '" + e.get_hostId() + "' is already registered.")
                }
                this.$a++;
                e.set_hostId(cf);
                this.$9[cf] = e;
                e.add_customViewsListLoad(ss.mkdel(this, this.$3));
                e.add_stateReadyForQuery(ss.mkdel(this, this.$5))
            }, unregisterHandler: function (e) {
                if (ss.isValue(e.get_hostId()) || ss.isValue(this.$9[e.get_hostId()])) {
                    delete this.$9[e.get_hostId()];
                    e.remove_customViewsListLoad(ss.mkdel(this, this.$3));
                    e.remove_stateReadyForQuery(ss.mkdel(this, this.$5))
                }
            }, sendCommand: function (e) {
                return function (cf, cg, ch) {
                    var ci = cf.get_iframe();
                    var cj = cf.get_hostId();
                    if (!K.hasWindowPostMessage() || ss.isNullOrUndefined(ci) || ss.isNullOrUndefined(ci.contentWindow)) {
                        return
                    }
                    var ck = p.generateNextCommandId();
                    var cl = this.$6[cj];
                    if (ss.isNullOrUndefined(cl)) {
                        cl = {};
                        this.$6[cj] = cl
                    }
                    cl[ck] = ch;
                    var cm = ch.get_commandName();
                    if (cm === 'api.ShowCustomViewCommand') {
                        var cn = this.$8[cj];
                        if (ss.isNullOrUndefined(cn)) {
                            cn = [];
                            this.$8[cj] = cn
                        }
                        cn.push(ch)
                    }
                    var co = null;
                    if (ss.isValue(cg)) {
                        co = JSON.stringify(cg)
                    }
                    var cp = new p(cm, ck, cj, co);
                    var cq = cp.serialize();
                    if (K.isPostMessageSynchronous()) {
                        window.setTimeout(function () {
                            ci.contentWindow.postMessage(cq, '*')
                        }, 0)
                    } else {
                        ci.contentWindow.postMessage(cq, '*')
                    }
                }
            }, $3: function (e) {
                var cf = e.get_hostId();
                var cg = this.$8[cf];
                if (ss.isNullOrUndefined(cg)) {
                    return
                }
                for (var ch = 0; ch < cg.length; ch++) {
                    var ci = cg[ch];
                    if (!ss.staticEquals(ci.get_successCallback(), null)) {
                        ci.get_successCallback()(null)
                    }
                }
                delete this.$8[cf]
            }, $5: function (e) {
                var cf = this.$7[e.get_hostId()];
                if (K.isNullOrEmpty(cf)) {
                    return
                }
                while (cf.length > 0) {
                    var cg = cf.pop();
                    if (ss.isValue(cg)) {
                        cg()
                    }
                }
            }, $1: function (e) {
                var cf = e;
                if (ss.isNullOrUndefined(cf.data)) {
                    return
                }
                var cg = p.parse(cf.data.toString());
                var ch = cg.get_rawName();
                var ci = cg.get_hostId();
                var cj = this.$9[ci];
                if (ss.isNullOrUndefined(cj) || !ss.referenceEquals(cj.get_hostId(), cg.get_hostId())) {
                    cj = this.$0(cf)
                }
                if (cg.get_isApiCommandName()) {
                    if (cg.get_commandId() === 'xdomainSourceId') {
                        cj.handleEventNotification(cg.get_name(), cg.get_parameters());
                        if (cg.get_name() === 'api.FirstVizSizeKnownEvent') {
                            cf.source.postMessage('tableau.bootstrap', '*')
                        }
                    } else {
                        this.$2(cg)
                    }
                } else {
                    this.$4(ch, cj)
                }
            }, $2: function (e) {
                var cf = this.$6[e.get_hostId()];
                var cg = (ss.isValue(cf) ? cf[e.get_commandId()] : null);
                if (ss.isNullOrUndefined(cg)) {
                    return
                }
                delete cf[e.get_commandId()];
                if (e.get_name() !== cg.get_commandName()) {
                    return
                }
                var ch = new s(e.get_parameters());
                var ci = ch.get_data();
                if (ch.get_result() === 'api.success') {
                    switch (cg.get_successCallbackTiming()) {
                        case 0: {
                            if (ss.isValue(cg.get_successCallback())) {
                                cg.get_successCallback()(ci)
                            }
                            break
                        }
                        case 1: {
                            var cj = function () {
                                if (ss.isValue(cg.get_successCallback())) {
                                    cg.get_successCallback()(ci)
                                }
                            };
                            var ck = this.$7[e.get_hostId()];
                            if (ss.isNullOrUndefined(ck)) {
                                ck = [];
                                this.$7[e.get_hostId()] = ck
                            }
                            ck.push(cj);
                            break
                        }
                        default: {
                            throw J.createInternalError('Unknown timing value: ' + cg.get_successCallbackTiming())
                        }
                    }
                } else if (ss.isValue(cg.get_errorCallback())) {
                    var cl = ch.get_result() === 'api.remotefailed';
                    var cm = (ss.isValue(ci) ? ci.toString() : '');
                    cg.get_errorCallback()(cl, cm)
                }
            }, $4: function (e, cf) {
                if (e === 'layoutInfoReq') {
                    L.$1()
                } else if (e === 'tableau.completed' || e === 'completed') {
                    cf.handleVizLoad()
                } else if (e === 'tableau.listening') {
                    cf.handleVizListening()
                }
            }, $0: function (e) {
                var cf = new ss.ObjectEnumerator(this.$9);
                try {
                    while (cf.moveNext()) {
                        var cg = cf.current();
                        if (this.$9.hasOwnProperty(cg.key) && ss.referenceEquals(cg.value.get_iframe().contentWindow, e.source)) {
                            return cg.value
                        }
                    }
                } finally {
                    cf.dispose()
                }
                return new c
            }
        }, null, [br]);
        ss.initInterface(bq, a, {
            add_customViewsListLoad: null,
            remove_customViewsListLoad: null,
            add_stateReadyForQuery: null,
            remove_stateReadyForQuery: null,
            get_iframe: null,
            get_hostId: null,
            set_hostId: null,
            handleVizLoad: null,
            handleVizListening: null,
            handleEventNotification: null
        });
        ss.initClass(c, a, {
            add_customViewsListLoad: function (e) {
                this.$1$1 = ss.delegateCombine(this.$1$1, e)
            }, remove_customViewsListLoad: function (e) {
                this.$1$1 = ss.delegateRemove(this.$1$1, e)
            }, add_stateReadyForQuery: function (e) {
                this.$1$2 = ss.delegateCombine(this.$1$2, e)
            }, remove_stateReadyForQuery: function (e) {
                this.$1$2 = ss.delegateRemove(this.$1$2, e)
            }, get_iframe: function () {
                return null
            }, get_hostId: function () {
                return this.$2
            }, set_hostId: function (e) {
                this.$2 = e
            }, $1: function () {
                return '*'
            }, handleVizLoad: function () {
            }, handleVizListening: function () {
            }, handleEventNotification: function (e, cf) {
            }, $0: function () {
                this.$1$1(null);
                this.$1$2(null)
            }
        }, null, [bq]);
        ss.initClass(bm, a, {
            get__workbookImpl: function () {
                return this.$0
            }, get__worksheetImpl: function () {
                return this.$1
            }
        });
        ss.initClass(d, a, {}, bm);
        ss.initClass(f, a, {
            get__parameterName: function () {
                return this.$2
            }
        }, bm);
        ss.initClass(g, a, {
            get__customViewImpl: function () {
                return this.$2
            }
        }, bm);
        ss.initClass(h, a, {
            get__filterFieldName: function () {
                return this.$3
            }, $2: function () {
                return this.$4
            }
        }, bm);
        ss.initClass(i, a, {}, bm);
        ss.initClass(j, a, {});
        ss.initClass(k, a, {});
        ss.initClass(l, a, {
            $2: function () {
                return this.$5
            }, $3: function () {
                return this.$6
            }, $1: function () {
                if (ss.isNullOrUndefined(this.$4)) {
                    this.$4 = this.$5._toApiCollection()
                }
                return this.$4
            }, $0: function (e) {
                this.$5._add(e.fieldName, e)
            }
        });
        ss.initClass(m, a, {
            $8: function () {
                if (ss.isNullOrUndefined(this.$i)) {
                    this.$i = new bS(this)
                }
                return this.$i
            }, $7: function () {
                return this.$h
            }, $2: function () {
                return this.$c
            }, $3: function () {
                return this.$d
            }, $1: function () {
                return this.$b
            }, $0: function () {
                return this.$a
            }, $6: function () {
                return this.$g
            }, $5: function () {
                return this.$f
            }, $9: function () {
                return this.$j
            }, $4: function () {
                return this.$e
            }
        });
        ss.initClass(n, a, {});
        ss.initClass(o, a, {});
        ss.initClass(p, a, {
            get_name: function () {
                return this.$1$1
            }, set_name: function (e) {
                this.$1$1 = e
            }, get_hostId: function () {
                return this.$1$2
            }, set_hostId: function (e) {
                this.$1$2 = e
            }, get_commandId: function () {
                return this.$1$3
            }, set_commandId: function (e) {
                this.$1$3 = e
            }, get_parameters: function () {
                return this.$1$4
            }, set_parameters: function (e) {
                this.$1$4 = e
            }, get_isApiCommandName: function () {
                return this.get_rawName().indexOf('api.', 0) === 0
            }, get_rawName: function () {
                return this.get_name().toString()
            }, serialize: function () {
                var e = [];
                e.push(this.get_name());
                e.push(this.get_commandId());
                e.push(this.get_hostId());
                if (ss.isValue(this.get_parameters())) {
                    e.push(this.get_parameters())
                }
                var cf = e.join(',');
                return cf
            }
        });
        ss.initClass(q, a, {});
        ss.initClass(r, a, {
            get_workbookName: function () {
                return this.$1
            }, get_worksheetName: function () {
                return this.$2
            }, get_data: function () {
                return this.$0
            }, serialize: function () {
                var e = {};
                e['api.workbookName'] = this.$1;
                e['api.worksheetName'] = this.$2;
                e['api.commandData'] = this.$0;
                return JSON.stringify(e)
            }
        });
        ss.initClass(s, a, {
            get_result: function () {
                return this.$1
            }, get_data: function () {
                return this.$0
            }
        });
        ss.initClass(t, a, {
            get__length: function () {
                return this.$4.length
            }, get__rawArray: function () {
                return this.$4
            }, get_item: function (e) {
                return this.$4[e]
            }, _get: function (e) {
                var cf = this.$0(e);
                if (ss.isValue(this.$3[cf])) {
                    return this.$3[cf]
                }
                return undefined
            }, _has: function (e) {
                return ss.isValue(this._get(e))
            }, _add: function (e, cf) {
                this.$1(e, cf);
                var cg = this.$0(e);
                this.$4.push(cf);
                this.$3[cg] = cf
            }, _addToFirst: function (e, cf) {
                this.$1(e, cf);
                var cg = this.$0(e);
                this.$4.unshift(cf);
                this.$3[cg] = cf
            }, _remove: function (e) {
                var cf = this.$0(e);
                if (ss.isValue(this.$3[cf])) {
                    var cg = this.$3[cf];
                    delete this.$3[cf];
                    for (var ch = 0; ch < this.$4.length; ch++) {
                        if (ss.referenceEquals(this.$4[ch], cg)) {
                            this.$4.splice(ch, 1);
                            break
                        }
                    }
                }
            }, _toApiCollection: function () {
                var e = this.$4.concat();
                e.get = ss.mkdel(this, function (cf) {
                    return this._get(cf)
                });
                e.has = ss.mkdel(this, function (cf) {
                    return this._has(cf)
                });
                return e
            }, $2: function (e) {
                if (K.isNullOrEmpty(e)) {
                    throw new ss.Exception('Null key')
                }
                if (this._has(e)) {
                    throw new ss.Exception("Duplicate key '" + e + "'")
                }
            }, $1: function (e, cf) {
                this.$2(e);
                if (ss.isNullOrUndefined(cf)) {
                    throw new ss.Exception('Null item')
                }
            }, $0: function (e) {
                return '_' + e
            }
        });
        ss.initClass(u, a, {
            get_fieldName: function () {
                return this.$1
            }, get_dataType: function () {
                return this.$0
            }, get_isReferenced: function () {
                return this.$3
            }, get_index: function () {
                return this.$2
            }
        });
        ss.initClass(v, a, {
            $5: function () {
                if (ss.isNullOrUndefined(this.$c)) {
                    this.$c = new bI(this)
                }
                return this.$c
            }, $b: function () {
                return this.$l.get_workbook()
            }, $a: function () {
                return this.$k
            }, $7: function () {
                return this.$h
            }, $8: function (e) {
                if (this.$f) {
                    throw J.create('staleDataReference', 'Stale data')
                }
                this.$h = e
            }, $9: function () {
                return this.$i
            }, $3: function () {
                return this.$e
            }, $4: function (e) {
                if (this.$f) {
                    throw J.create('staleDataReference', 'Stale data')
                }
                this.$e = e
            }, $6: function () {
                return this.$d
            }, $2: function () {
                if (this.$f || ss.isNullOrUndefined(this.$j)) {
                    throw J.create('staleDataReference', 'Stale data')
                }
                this.$j.isPublic = this.$e;
                this.$j.name = this.$h;
                var e = new tab._Deferred;
                var cf = {};
                cf['api.customViewParam'] = this.$j;
                var cg = v.$0('api.UpdateCustomViewCommand', e, ss.mkdel(this, function (ch) {
                    v._processCustomViewUpdate(this.$l, this.$g, ch, true);
                    e.resolve(this.$5())
                }));
                this.$g.sendCommand(Object).call(this.$g, cf, cg);
                return e.get_promise()
            }, $1: function () {
                var e = new tab._Deferred;
                var cf = {};
                cf['api.customViewParam'] = this.$j;
                var cg = v.$0('api.RemoveCustomViewCommand', e, ss.mkdel(this, function (ch) {
                    this.$f = true;
                    v._processCustomViews(this.$l, this.$g, ch);
                    e.resolve(this.$5())
                }));
                this.$g.sendCommand(Object).call(this.$g, cf, cg);
                return e.get_promise()
            }, _showAsync: function () {
                if (this.$f || ss.isNullOrUndefined(this.$j)) {
                    throw J.create('staleDataReference', 'Stale data')
                }
                return v._showCustomViewAsync(this.$l, this.$g, this.$j)
            }, $0: function (e) {
                return !ss.referenceEquals(this.$i, e.$i) || !ss.referenceEquals(this.$k, e.$k) || this.$e !== e.$e || this.$d !== e.$d
            }
        });
        ss.initClass(E, a, {
            get_sheet: null, get_name: function () {
                return this.$5
            }, get_index: function () {
                return this.$1
            }, get_workbookImpl: function () {
                return this.$a
            }, get_workbook: function () {
                return this.$a.get_workbook()
            }, get_url: function () {
                if (this.$3) {
                    throw J.createNoUrlForHiddenWorksheet()
                }
                return this.$9
            }, get_size: function () {
                return this.$8
            }, get_isHidden: function () {
                return this.$3
            }, get_isActive: function () {
                return this.$2
            }, set_isActive: function (e) {
                this.$2 = e
            }, get_isDashboard: function () {
                return this.$7 === 'dashboard'
            }, get_isStory: function () {
                return this.$7 === 'story'
            }, get_sheetType: function () {
                return this.$7
            }, get_parentStoryPoint: function () {
                if (ss.isValue(this.$6)) {
                    return this.$6.get_storyPoint()
                }
                return null
            }, get_parentStoryPointImpl: function () {
                return this.$6
            }, set_parentStoryPointImpl: function (e) {
                if (this.$7 === 'story') {
                    throw J.createInternalError('A story cannot be a child of another story.')
                }
                this.$6 = e
            }, get_zoneId: function () {
                return this.$b
            }, get_messagingOptions: function () {
                return this.$4
            }, changeSizeAsync: function (e) {
                e = E.$1(e);
                if (this.$7 === 'worksheet' && e.behavior !== 'automatic') {
                    throw J.createInvalidSizeBehaviorOnWorksheet()
                }
                var cf = new tab._Deferred;
                if (this.$8.behavior === e.behavior && e.behavior === 'automatic') {
                    cf.resolve(e);
                    return cf.get_promise()
                }
                var cg = this.$0(e);
                var ch = {};
                ch['api.setSheetSizeName'] = this.$5;
                ch['api.minWidth'] = cg['api.minWidth'];
                ch['api.minHeight'] = cg['api.minHeight'];
                ch['api.maxWidth'] = cg['api.maxWidth'];
                ch['api.maxHeight'] = cg['api.maxHeight'];
                var ci = new (ss.makeGenericType(bh, [Object]))('api.SetSheetSizeCommand', 1, ss.mkdel(this, function (cj) {
                    this.get_workbookImpl()._update(ss.mkdel(this, function () {
                        var ck = this.get_workbookImpl().get_publishedSheets()._get(this.get_name()).getSize();
                        cf.resolve(ck)
                    }))
                }), function (cj, ck) {
                    cf.reject(J.createServerError(ck))
                });
                this.sendCommand(Object).call(this, ch, ci);
                return cf.get_promise()
            }, sendCommand: function (e) {
                return function (cf, cg) {
                    this.$4.sendCommand(e).call(this.$4, cf, cg)
                }
            }, $0: function (e) {
                var cf = null;
                if (ss.isNullOrUndefined(e) || ss.isNullOrUndefined(e.behavior) || e.behavior !== 'automatic' && ss.isNullOrUndefined(e.minSize) && ss.isNullOrUndefined(e.maxSize)) {
                    throw J.createInvalidSheetSizeParam()
                }
                var cg = 0;
                var ch = 0;
                var ci = 0;
                var cj = 0;
                var ck = {};
                ck['api.minWidth'] = 0;
                ck['api.minHeight'] = 0;
                ck['api.maxWidth'] = 0;
                ck['api.maxHeight'] = 0;
                if (e.behavior === 'automatic') {
                    cf = bv.$ctor('automatic', undefined, undefined)
                } else if (e.behavior === 'atmost') {
                    if (ss.isNullOrUndefined(e.maxSize) || ss.isNullOrUndefined(e.maxSize.width) || ss.isNullOrUndefined(e.maxSize.height)) {
                        throw J.createMissingMaxSize()
                    }
                    if (e.maxSize.width < 0 || e.maxSize.height < 0) {
                        throw J.createInvalidSizeValue()
                    }
                    ck['api.maxWidth'] = e.maxSize.width;
                    ck['api.maxHeight'] = e.maxSize.height;
                    cf = bv.$ctor('atmost', undefined, e.maxSize)
                } else if (e.behavior === 'atleast') {
                    if (ss.isNullOrUndefined(e.minSize) || ss.isNullOrUndefined(e.minSize.width) || ss.isNullOrUndefined(e.minSize.height)) {
                        throw J.createMissingMinSize()
                    }
                    if (e.minSize.width < 0 || e.minSize.height < 0) {
                        throw J.createInvalidSizeValue()
                    }
                    ck['api.minWidth'] = e.minSize.width;
                    ck['api.minHeight'] = e.minSize.height;
                    cf = bv.$ctor('atleast', e.minSize, undefined)
                } else if (e.behavior === 'range') {
                    if (ss.isNullOrUndefined(e.minSize) || ss.isNullOrUndefined(e.maxSize) || ss.isNullOrUndefined(e.minSize.width) || ss.isNullOrUndefined(e.maxSize.width) || ss.isNullOrUndefined(e.minSize.height) || ss.isNullOrUndefined(e.maxSize.height)) {
                        throw J.createMissingMinMaxSize()
                    }
                    if (e.minSize.width < 0 || e.minSize.height < 0 || e.maxSize.width < 0 || e.maxSize.height < 0 || e.minSize.width > e.maxSize.width || e.minSize.height > e.maxSize.height) {
                        throw J.createInvalidRangeSize()
                    }
                    ck['api.minWidth'] = e.minSize.width;
                    ck['api.minHeight'] = e.minSize.height;
                    ck['api.maxWidth'] = e.maxSize.width;
                    ck['api.maxHeight'] = e.maxSize.height;
                    cf = bv.$ctor('range', e.minSize, e.maxSize)
                } else if (e.behavior === 'exactly') {
                    if (ss.isValue(e.minSize) && ss.isValue(e.maxSize) && ss.isValue(e.minSize.width) && ss.isValue(e.maxSize.width) && ss.isValue(e.minSize.height) && ss.isValue(e.maxSize.height)) {
                        cg = e.minSize.width;
                        ch = e.minSize.height;
                        ci = e.maxSize.width;
                        cj = e.maxSize.height;
                        if (cg !== ci || ch !== cj) {
                            throw J.createSizeConflictForExactly()
                        }
                    } else if (ss.isValue(e.minSize) && ss.isValue(e.minSize.width) && ss.isValue(e.minSize.height)) {
                        cg = e.minSize.width;
                        ch = e.minSize.height;
                        ci = cg;
                        cj = ch
                    } else if (ss.isValue(e.maxSize) && ss.isValue(e.maxSize.width) && ss.isValue(e.maxSize.height)) {
                        ci = e.maxSize.width;
                        cj = e.maxSize.height;
                        cg = ci;
                        ch = cj
                    }
                    ck['api.minWidth'] = cg;
                    ck['api.minHeight'] = ch;
                    ck['api.maxWidth'] = ci;
                    ck['api.maxHeight'] = cj;
                    cf = bv.$ctor('exactly', bx.$ctor(cg, ch), bx.$ctor(ci, cj))
                }
                this.$8 = cf;
                return ck
            }
        });
        ss.initClass(w, a, {
            get_sheet: function () {
                return this.get_dashboard()
            }, get_dashboard: function () {
                if (ss.isNullOrUndefined(this.$d)) {
                    this.$d = new bJ(this)
                }
                return this.$d
            }, get_worksheets: function () {
                return this.$f
            }, get_objects: function () {
                return this.$e
            }, $c: function (e, cf) {
                this.$e = new tab._Collection;
                this.$f = new tab._Collection;
                for (var cg = 0; cg < e.length; cg++) {
                    var ch = e[cg];
                    var ci = null;
                    if (e[cg].objectType === 'worksheet') {
                        var cj = ch.name;
                        if (ss.isNullOrUndefined(cj)) {
                            continue
                        }
                        var ck = this.$f.get__length();
                        var cl = bw.createAutomatic();
                        var cm = false;
                        var cn = cf(cj);
                        var co = ss.isNullOrUndefined(cn);
                        var cp = (co ? '' : cn.getUrl());
                        var cq = F.$ctor(cj, 'worksheet', ck, cl, this.get_workbook(), cp, cm, co, ch.zoneId);
                        var cr = new O(cq, this.get_workbookImpl(), this.get_messagingOptions(), this);
                        ci = cr.get_worksheet();
                        this.$f._add(cj, cr.get_worksheet())
                    }
                    var cs = new bK(ch, this.get_dashboard(), ci);
                    this.$e._add(cg.toString(), cs)
                }
            }
        }, E);
        ss.initClass(x, a, {
            get_dataSource: function () {
                if (ss.isNullOrUndefined(this.$0)) {
                    this.$0 = new bL(this)
                }
                return this.$0
            }, get_name: function () {
                return this.$3
            }, get_fields: function () {
                return this.$1
            }, get_isPrimary: function () {
                return this.$2
            }, addField: function (e) {
                this.$1._add(e.getName(), e)
            }
        });
        ss.initClass(y, a, {
            get_name: function () {
                return this.$2
            }, get_rows: function () {
                return this.$3
            }, get_columns: function () {
                return this.$0
            }, get_totalRowCount: function () {
                return this.$4
            }, get_isSummaryData: function () {
                return this.$1
            }
        });
        ss.initClass(z, a, {
            get_promise: function () {
                return this.$3
            }, all: function (e) {
                var cf = new z;
                var cg = e.length;
                var ch = cg;
                var ci = [];
                if (cg === 0) {
                    cf.resolve(ci);
                    return cf.get_promise()
                }
                var cj = function (cl, cm) {
                    var cn = k.$0(cl);
                    cn.then(function (co) {
                        ci[cm] = co;
                        ch--;
                        if (ch === 0) {
                            cf.resolve(ci)
                        }
                        return null
                    }, function (co) {
                        cf.reject(co);
                        return null
                    })
                };
                for (var ck = 0; ck < cg; ck++) {
                    cj(e[ck], ck)
                }
                return cf.get_promise()
            }, then: function (e, cf) {
                return this.$5(e, cf)
            }, resolve: function (e) {
                return this.$4(e)
            }, reject: function (e) {
                return this.$4(k.$3(e))
            }, $0: function (e, cf) {
                var cg = new z;
                this.$2.push(function (ch) {
                    ch.then(e, cf).then(ss.mkdel(cg, cg.resolve), ss.mkdel(cg, cg.reject))
                });
                return cg.get_promise()
            }, $1: function (e) {
                var cf = k.$0(e);
                this.$5 = cf.then;
                this.$4 = k.$0;
                for (var cg = 0; cg < this.$2.length; cg++) {
                    var ch = this.$2[cg];
                    ch(cf)
                }
                this.$2 = null;
                return cf
            }
        });
        ss.initClass(A, a, {});
        ss.initClass(B, a, {});
        ss.initClass(C, a, {
            always: function (e) {
                return this.then(e, e)
            }, otherwise: function (e) {
                return this.then(null, e)
            }
        });
        ss.initClass(D, a, {
            intersect: function (e) {
                var cf = Math.max(this.left, e.left);
                var cg = Math.max(this.top, e.top);
                var ch = Math.min(this.left + this.width, e.left + e.width);
                var ci = Math.min(this.top + this.height, e.top + e.height);
                if (ch <= cf || ci <= cg) {
                    return new D(0, 0, 0, 0)
                }
                return new D(cf, cg, ch - cf, ci - cg)
            }
        });
        ss.initClass(F, a, {}, Object);
        ss.initClass(G, a, {
            add_activeStoryPointChange: function (e) {
                this.$2$1 = ss.delegateCombine(this.$2$1, e)
            }, remove_activeStoryPointChange: function (e) {
                this.$2$1 = ss.delegateRemove(this.$2$1, e)
            }, get_activeStoryPointImpl: function () {
                return this.$g
            }, get_sheet: function () {
                return this.get_story()
            }, get_story: function () {
                if (ss.isNullOrUndefined(this.$i)) {
                    this.$i = new bX(this)
                }
                return this.$i
            }, get_storyPointsInfo: function () {
                return this.$j
            }, update: function (e) {
                var cf = null;
                var cg = null;
                this.$j = this.$j || new Array(e.storyPoints.length);
                for (var ch = 0; ch < e.storyPoints.length; ch++) {
                    var ci = e.storyPoints[ch];
                    var cj = ci.caption;
                    var ck = ch === e.activeStoryPointIndex;
                    var cl = I.$ctor(cj, ch, ci.storyPointId, ck, ci.isUpdated, this);
                    if (ss.isNullOrUndefined(this.$j[ch])) {
                        this.$j[ch] = new bZ(cl)
                    } else if (this.$j[ch]._impl.storyPointId === cl.storyPointId) {
                        var cm = this.$j[ch]._impl;
                        cm.caption = cl.caption;
                        cm.index = cl.index;
                        cm.isActive = ck;
                        cm.isUpdated = cl.isUpdated
                    } else {
                        this.$j[ch] = new bZ(cl)
                    }
                    if (ck) {
                        cf = ci.containedSheetInfo;
                        cg = cl
                    }
                }
                var cn = this.$j.length - e.storyPoints.length;
                this.$j.splice(e.storyPoints.length, cn);
                var co = ss.isNullOrUndefined(this.$g) || this.$g.get_storyPointId() !== cg.storyPointId;
                if (ss.isValue(this.$g) && co) {
                    this.$g.set_isActive(false)
                }
                var cp = this.$g;
                if (co) {
                    var cq = H.createContainedSheet(cf, this.get_workbookImpl(), this.get_messagingOptions(), this.$h);
                    this.$g = new H(cg, cq)
                } else {
                    this.$g.set_isActive(cg.isActive);
                    this.$g.set_isUpdated(cg.isUpdated)
                }
                if (co && ss.isValue(cp)) {
                    this.$d(this.$j[cp.get_index()], this.$g.get_storyPoint())
                }
            }, activatePreviousStoryPointAsync: function () {
                return this.$c('api.ActivatePreviousStoryPoint')
            }, activateNextStoryPointAsync: function () {
                return this.$c('api.ActivateNextStoryPoint')
            }, activateStoryPointAsync: function (e) {
                var cf = new tab._Deferred;
                if (e < 0 || e >= this.$j.length) {
                    throw J.createIndexOutOfRange(e)
                }
                var cg = this.get_activeStoryPointImpl();
                var ch = {};
                ch['api.storyPointIndex'] = e;
                var ci = new (ss.makeGenericType(bh, [Object]))('api.ActivateStoryPoint', 0, ss.mkdel(this, function (cj) {
                    this.$e(cg, cj);
                    cf.resolve(this.$g.get_storyPoint())
                }), function (cj, ck) {
                    cf.reject(J.createServerError(ck))
                });
                this.sendCommand(Object).call(this, ch, ci);
                return cf.get_promise()
            }, revertStoryPointAsync: function (e) {
                e = e || this.$g.get_index();
                if (e < 0 || e >= this.$j.length) {
                    throw J.createIndexOutOfRange(e)
                }
                var cf = new tab._Deferred;
                var cg = {};
                cg['api.storyPointIndex'] = e;
                var ch = new (ss.makeGenericType(bh, [Object]))('api.RevertStoryPoint', 0, ss.mkdel(this, function (ci) {
                    this.$f(e, ci);
                    cf.resolve(this.$j[e])
                }), function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $c: function (e) {
                if (e !== 'api.ActivatePreviousStoryPoint' && e !== 'api.ActivateNextStoryPoint') {
                    throw J.createInternalError("commandName '" + e + "' is invalid.")
                }
                var cf = new tab._Deferred;
                var cg = this.get_activeStoryPointImpl();
                var ch = {};
                var ci = new (ss.makeGenericType(bh, [Object]))(e, 0, ss.mkdel(this, function (cj) {
                    this.$e(cg, cj);
                    cf.resolve(this.$g.get_storyPoint())
                }), function (cj, ck) {
                    cf.reject(J.createServerError(ck))
                });
                this.sendCommand(Object).call(this, ch, ci);
                return cf.get_promise()
            }, $f: function (e, cf) {
                var cg = this.$j[e]._impl;
                if (cg.storyPointId !== cf.storyPointId) {
                    throw J.createInternalError("We should not be updating a story point where the IDs don't match. Existing storyPointID=" + cg.storyPointId + ', newStoryPointID=' + cf.storyPointId)
                }
                cg.caption = cf.caption;
                cg.isUpdated = cf.isUpdated;
                if (cf.storyPointId === this.$g.get_storyPointId()) {
                    this.$g.set_isUpdated(cf.isUpdated)
                }
            }, $e: function (e, cf) {
                var cg = cf.index;
                if (e.get_index() === cg) {
                    return
                }
                var ch = this.$j[e.get_index()];
                var ci = this.$j[cg]._impl;
                var cj = H.createContainedSheet(cf.containedSheetInfo, this.get_workbookImpl(), this.get_messagingOptions(), this.$h);
                ci.isActive = true;
                this.$g = new H(ci, cj);
                e.set_isActive(false);
                ch._impl.isActive = false;
                this.$d(ch, this.$g.get_storyPoint())
            }, $d: function (e, cf) {
                if (!ss.staticEquals(this.$2$1, null)) {
                    this.$2$1(e, cf)
                }
            }
        }, E);
        ss.initClass(H, a, {
            get_caption: function () {
                return this.$1
            }, get_containedSheetImpl: function () {
                return this.$2
            }, get_index: function () {
                return this.$3
            }, get_isActive: function () {
                return this.$4
            }, set_isActive: function (e) {
                this.$4 = e
            }, get_isUpdated: function () {
                return this.$5
            }, set_isUpdated: function (e) {
                this.$5 = e
            }, get_parentStoryImpl: function () {
                return this.$6
            }, get_storyPoint: function () {
                if (ss.isNullOrUndefined(this.$7)) {
                    this.$7 = new bY(this)
                }
                return this.$7
            }, get_storyPointId: function () {
                return this.$8
            }, $0: function () {
                return I.$ctor(this.$1, this.$3, this.$8, this.$4, this.$5, this.$6)
            }
        });
        ss.initClass(I, a, {}, Object);
        ss.initClass(J, a, {});
        ss.initClass(K, a, {});
        ss.initClass(L, a, {});
        ss.initClass(M, a, {
            get_url: function () {
                return this.$0()
            }, get_baseUrl: function () {
                return this.$2
            }, $0: function () {
                var e = [];
                e.push(this.get_baseUrl());
                e.push('?');
                if (this.userSuppliedParameters.length > 0) {
                    e.push(this.userSuppliedParameters);
                    e.push('&')
                }
                var cf = !this.fixedSize && !(this.userSuppliedParameters.indexOf(':size=') !== -1) && this.parentElement.clientWidth * this.parentElement.clientHeight > 0;
                if (cf) {
                    e.push(':size=');
                    e.push(this.parentElement.clientWidth + ',' + this.parentElement.clientHeight);
                    e.push('&')
                }
                e.push(':embed=y');
                e.push('&:showVizHome=n');
                if (!this.fixedSize) {
                    e.push('&:bootstrapWhenNotified=y')
                }
                if (!this.tabs) {
                    e.push('&:tabs=n')
                }
                if (this.displayStaticImage) {
                    e.push('&:display_static_image=y')
                }
                if (!this.toolbar) {
                    e.push('&:toolbar=n')
                } else if (!ss.isNullOrUndefined(this.toolBarPosition)) {
                    e.push('&:toolbar=');
                    e.push(this.toolBarPosition.toString())
                }
                if (ss.isValue(this.device)) {
                    e.push('&:device=');
                    e.push(this.device.toString())
                }
                var cg = this.$1;
                var ch = new ss.ObjectEnumerator(cg);
                try {
                    while (ch.moveNext()) {
                        var ci = ch.current();
                        if (ci.key !== 'embed' && ci.key !== 'height' && ci.key !== 'width' && ci.key !== 'device' && ci.key !== 'autoSize' && ci.key !== 'hideTabs' && ci.key !== 'hideToolbar' && ci.key !== 'onFirstInteractive' && ci.key !== 'onFirstVizSizeKnown' && ci.key !== 'toolbarPosition' && ci.key !== 'instanceIdToClone' && ci.key !== 'display_static_image') {
                            e.push('&');
                            e.push(encodeURIComponent(ci.key));
                            e.push('=');
                            e.push(encodeURIComponent(ci.value.toString()))
                        }
                    }
                } finally {
                    ch.dispose()
                }
                e.push('&:apiID=' + this.hostId);
                if (ss.isValue(this.$1.instanceIdToClone)) {
                    e.push('#' + this.$1.instanceIdToClone)
                }
                return e.join('')
            }
        });
        ss.initClass(N, a, {
            get_workbook: function () {
                if (ss.isNullOrUndefined(this.$E)) {
                    this.$E = new cd(this)
                }
                return this.$E
            }, get_viz: function () {
                return this.$D.$15()
            }, get_publishedSheets: function () {
                return this.$A
            }, get_name: function () {
                return this.$y
            }, get_activeSheetImpl: function () {
                return this.$s
            }, get_activeCustomView: function () {
                return this.$t
            }, get_isDownloadAllowed: function () {
                return this.$v
            }, $4: function (e) {
                if (ss.isNullOrUndefined(this.$s)) {
                    return null
                }
                var cf = N.$2(e);
                if (ss.isNullOrUndefined(cf)) {
                    return null
                }
                if (ss.referenceEquals(cf, this.$s.get_name())) {
                    return this.$s
                }
                if (this.$s.get_isDashboard()) {
                    var cg = this.$s;
                    var ch = cg.get_worksheets()._get(cf);
                    if (ss.isValue(ch)) {
                        return ch._impl
                    }
                }
                return null
            }, _setActiveSheetAsync: function (e) {
                if (K.isNumber(e)) {
                    var cf = e;
                    if (cf < this.$A.get__length() && cf >= 0) {
                        return this.$1(this.$A.get_item(cf).$0)
                    } else {
                        throw J.createIndexOutOfRange(cf)
                    }
                }
                var cg = N.$2(e);
                var ch = this.$A._get(cg);
                if (ss.isValue(ch)) {
                    return this.$1(ch.$0)
                } else if (this.$s.get_isDashboard()) {
                    var ci = this.$s;
                    var cj = ci.get_worksheets()._get(cg);
                    if (ss.isValue(cj)) {
                        this.$r = null;
                        var ck = '';
                        if (cj.getIsHidden()) {
                            this.$r = cj._impl
                        } else {
                            ck = cj._impl.get_url()
                        }
                        return this.$0(cj._impl.get_name(), ck)
                    }
                }
                throw J.create('sheetNotInWorkbook', 'Sheet is not found in Workbook')
            }, _revertAllAsync: function () {
                var e = new tab._Deferred;
                var cf = new (ss.makeGenericType(bh, [Object]))('api.RevertAllCommand', 1, function (cg) {
                    e.resolve()
                }, function (cg, ch) {
                    e.reject(J.createServerError(ch))
                });
                this.$d(Object).call(this, null, cf);
                return e.get_promise()
            }, _update: function (e) {
                this.$5(e)
            }, $1: function (e) {
                return this.$0(e.name, e.url)
            }, $0: function (e, cf) {
                var cg = new tab._Deferred;
                if (ss.isValue(this.$s) && ss.referenceEquals(e, this.$s.get_name())) {
                    cg.resolve(this.$s.get_sheet());
                    return cg.get_promise()
                }
                var ch = {};
                ch['api.switchToSheetName'] = e;
                ch['api.switchToRepositoryUrl'] = cf;
                ch['api.oldRepositoryUrl'] = this.$s.get_url();
                var ci = new (ss.makeGenericType(bh, [Object]))('api.SwitchActiveSheetCommand', 0, ss.mkdel(this, function (cj) {
                    this.$D.$18 = ss.mkdel(this, function () {
                        this.$D.$18 = null;
                        cg.resolve(this.$s.get_sheet())
                    })
                }), function (cj, ck) {
                    cg.reject(J.createServerError(ck))
                });
                this.$d(Object).call(this, ch, ci);
                return cg.get_promise()
            }, _updateActiveSheetAsync: function () {
                var e = new tab._Deferred;
                var cf = {};
                cf['api.switchToSheetName'] = this.$s.get_name();
                cf['api.switchToRepositoryUrl'] = this.$s.get_url();
                cf['api.oldRepositoryUrl'] = this.$s.get_url();
                var cg = new (ss.makeGenericType(bh, [Object]))('api.UpdateActiveSheetCommand', 0, ss.mkdel(this, function (ch) {
                    e.resolve(this.$s.get_sheet())
                }), function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.$d(Object).call(this, cf, cg);
                return e.get_promise()
            }, $d: function (e) {
                return function (cf, cg) {
                    this.$x.sendCommand(e).call(this.$x, cf, cg)
                }
            }, $5: function (e) {
                var cf = new (ss.makeGenericType(bh, [Object]))('api.GetClientInfoCommand', 0, ss.mkdel(this, function (cg) {
                    this.$a(cg);
                    if (ss.isValue(e)) {
                        e()
                    }
                }), null);
                this.$d(Object).call(this, null, cf)
            }, $a: function (e) {
                this.$y = e.workbookName;
                this.$v = e.isDownloadAllowed;
                this.$D.$N(!e.isAutoUpdate);
                this.$D.set_instanceId(e.instanceId);
                this.$3(e);
                this.$9(e)
            }, $9: function (e) {
                var cf = e.currentSheetName;
                var cg = this.$A._get(cf);
                if (ss.isNullOrUndefined(cg) && ss.isNullOrUndefined(this.$r)) {
                    throw J.createInternalError('The active sheet was not specified in baseSheets')
                }
                if (ss.isValue(this.$s) && ss.referenceEquals(this.$s.get_name(), cf)) {
                    return
                }
                if (ss.isValue(this.$s)) {
                    this.$s.set_isActive(false);
                    var ch = this.$A._get(this.$s.get_name());
                    if (ss.isValue(ch)) {
                        ch.$0.isActive = false
                    }
                    if (this.$s.get_sheetType() === 'story') {
                        var ci = this.$s;
                        ci.remove_activeStoryPointChange(ss.mkdel(this.$D, this.$D.raiseStoryPointSwitch))
                    }
                }
                if (ss.isValue(this.$r)) {
                    var cj = F.$ctor(this.$r.get_name(), 'worksheet', -1, this.$r.get_size(), this.get_workbook(), '', true, true, 4294967295);
                    this.$r = null;
                    this.$s = new O(cj, this, this.$x, null)
                } else {
                    var ck = null;
                    for (var cl = 0, cm = e.publishedSheets.length; cl < cm; cl++) {
                        if (ss.referenceEquals(e.publishedSheets[cl].name, cf)) {
                            ck = e.publishedSheets[cl];
                            break
                        }
                    }
                    if (ss.isNullOrUndefined(ck)) {
                        throw J.createInternalError('No base sheet was found corresponding to the active sheet.')
                    }
                    var cn = ss.mkdel(this, function (cr) {
                        return this.$A._get(cr)
                    });
                    if (ck.sheetType === 'dashboard') {
                        var co = new w(cg.$0, this, this.$x);
                        this.$s = co;
                        var cp = N.$0(e.dashboardZones);
                        co.$c(cp, cn)
                    } else if (ck.sheetType === 'story') {
                        var cq = new G(cg.$0, this, this.$x, e.story, cn);
                        this.$s = cq;
                        cq.add_activeStoryPointChange(ss.mkdel(this.$D, this.$D.raiseStoryPointSwitch))
                    } else {
                        this.$s = new O(cg.$0, this, this.$x, null)
                    }
                    cg.$0.isActive = true
                }
                this.$s.set_isActive(true)
            }, $3: function (e) {
                var cf = e.publishedSheets;
                if (ss.isNullOrUndefined(cf)) {
                    return
                }
                for (var cg = 0; cg < cf.length; cg++) {
                    var ch = cf[cg];
                    var ci = ch.name;
                    var cj = this.$A._get(ci);
                    var ck = N.$1(ch);
                    if (ss.isNullOrUndefined(cj)) {
                        var cl = ss.referenceEquals(ci, e.currentSheetName);
                        var cm = S.convertSheetType(ch.sheetType);
                        var cn = F.$ctor(ci, cm, cg, ck, this.get_workbook(), ch.repositoryUrl, cl, false, 4294967295);
                        cj = new bW(cn);
                        this.$A._add(ci, cj)
                    } else {
                        cj.$0.size = ck
                    }
                }
            }, $i: function () {
                return this.$u
            }, $j: function (e) {
                this.$u = e
            }, $p: function () {
                return this.$C
            }, $q: function (e) {
                this.$C = e
            }, $n: function () {
                return this.$B
            }, $o: function (e) {
                this.$B = e
            }, $g: function () {
                return this.$t
            }, $h: function (e) {
                this.$t = e
            }, $6: function () {
                return v._getCustomViewsAsync(this, this.$x)
            }, $f: function (e) {
                if (ss.isNullOrUndefined(e) || K.isNullOrEmpty(e)) {
                    return v._showCustomViewAsync(this, this.$x, null)
                } else {
                    var cf = this.$u._get(e);
                    if (ss.isNullOrUndefined(cf)) {
                        var cg = new tab._Deferred;
                        cg.reject(J.createInvalidCustomViewName(e));
                        return cg.get_promise()
                    }
                    return cf._impl._showAsync()
                }
            }, $c: function (e) {
                if (K.isNullOrEmpty(e)) {
                    throw J.createNullOrEmptyParameter('customViewName')
                }
                var cf = this.$u._get(e);
                if (ss.isNullOrUndefined(cf)) {
                    var cg = new tab._Deferred;
                    cg.reject(J.createInvalidCustomViewName(e));
                    return cg.get_promise()
                }
                return cf._impl.$1()
            }, $b: function (e) {
                if (K.isNullOrEmpty(e)) {
                    throw J.createInvalidParameter('customViewName')
                }
                return v._saveNewAsync(this, this.$x, e)
            }, $e: function () {
                return v._makeCurrentCustomViewDefaultAsync(this, this.$x)
            }, $k: function () {
                return this.$w
            }, $l: function (e) {
                this.$w = e
            }, $m: function () {
                return this.$z
            }, $8: function (e) {
                var cf = new tab._Deferred;
                if (ss.isValue(this.$w)) {
                    cf.resolve(this.$w.$8());
                    return cf.get_promise()
                }
                var cg = {};
                var ch = new (ss.makeGenericType(bh, [Object]))('api.FetchParametersCommand', 0, ss.mkdel(this, function (ci) {
                    var cj = N.$3(e, ci);
                    this.$w = cj;
                    cf.resolve(cj.$8())
                }), function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.$d(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $7: function () {
                var e = new tab._Deferred;
                var cf = {};
                var cg = new (ss.makeGenericType(bh, [Object]))('api.FetchParametersCommand', 0, ss.mkdel(this, function (ch) {
                    this.$z = N.$4(ch);
                    e.resolve(this.$m()._toApiCollection())
                }), function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.$d(Object).call(this, cf, cg);
                return e.get_promise()
            }, $2: function (e, cf) {
                var cg = new tab._Deferred;
                var ch = null;
                if (ss.isValue(this.$z)) {
                    if (ss.isNullOrUndefined(this.$z._get(e))) {
                        cg.reject(J.createInvalidParameter(e));
                        return cg.get_promise()
                    }
                    ch = this.$z._get(e)._impl;
                    if (ss.isNullOrUndefined(ch)) {
                        cg.reject(J.createInvalidParameter(e));
                        return cg.get_promise()
                    }
                }
                var ci = {};
                ci['api.setParameterName'] = (ss.isValue(this.$z) ? ch.$7() : e);
                if (ss.isValue(cf) && K.isDate(cf)) {
                    var cj = cf;
                    var ck = K.serializeDateForServer(cj);
                    ci['api.setParameterValue'] = ck
                } else {
                    ci['api.setParameterValue'] = (ss.isValue(cf) ? cf.toString() : null)
                }
                this.$w = null;
                var cl = new (ss.makeGenericType(bh, [Object]))('api.SetParameterValueCommand', 0, ss.mkdel(this, function (cm) {
                    if (ss.isNullOrUndefined(cm)) {
                        cg.reject(J.create('serverError', 'server error'));
                        return
                    }
                    if (!cm.isValidPresModel) {
                        cg.reject(J.createInvalidParameter(e));
                        return
                    }
                    var cn = new m(cm);
                    this.$w = cn;
                    cg.resolve(cn.$8())
                }), function (cm, cn) {
                    cg.reject(J.createInvalidParameter(e))
                });
                this.$d(Object).call(this, ci, cl);
                return cg.get_promise()
            }
        });
        ss.initClass(O, a, {
            get_sheet: function () {
                return this.get_worksheet()
            }, get_worksheet: function () {
                if (ss.isNullOrUndefined(this.$K)) {
                    this.$K = new ce(this)
                }
                return this.$K
            }, get_parentDashboardImpl: function () {
                return this.$I
            }, get_parentDashboard: function () {
                if (ss.isValue(this.$I)) {
                    return this.$I.get_dashboard()
                }
                return null
            }, $r: function () {
                this.$G();
                var e = new tab._Deferred;
                var cf = {};
                cf['api.worksheetName'] = this.get_name();
                var cg = new (ss.makeGenericType(bh, [Object]))('api.GetDataSourcesCommand', 0, function (ch) {
                    var ci = x.processDataSourcesForWorksheet(ch);
                    e.resolve(ci._toApiCollection())
                }, function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.sendCommand(Object).call(this, cf, cg);
                return e.get_promise()
            }, $q: function (e) {
                this.$G();
                var cf = new tab._Deferred;
                var cg = {};
                cg['api.dataSourceName'] = e;
                cg['api.worksheetName'] = this.get_name();
                var ch = new (ss.makeGenericType(bh, [Object]))('api.GetDataSourceCommand', 0, function (ci) {
                    var cj = x.processDataSource(ci);
                    if (ss.isValue(cj)) {
                        cf.resolve(cj.get_dataSource())
                    } else {
                        cf.reject(J.createServerError("Data source '" + e + "' not found"))
                    }
                }, function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $G: function () {
                var e = this.get_isActive();
                var cf = ss.isValue(this.$I) && this.$I.get_isActive();
                var cg = ss.isValue(this.get_parentStoryPointImpl()) && this.get_parentStoryPointImpl().get_parentStoryImpl().get_isActive();
                if (!e && !cf && !cg) {
                    throw J.createNotActiveSheet()
                }
            }, $d: function (e) {
                if (ss.isValue(this.get_parentStoryPointImpl())) {
                    var cf = {};
                    cf.AVP = this.get_name();
                    cf.XwZ = (ss.isValue(this.get_parentDashboardImpl()) ? this.$I.get_name() : this.get_name());
                    cf.WIZ = this.get_parentStoryPointImpl().get_containedSheetImpl().get_zoneId();
                    cf.Hna = this.get_parentStoryPointImpl().get_parentStoryImpl().get_name();
                    cf.hVl = this.get_parentStoryPointImpl().get_storyPointId();
                    e['api.visualId'] = cf
                } else {
                    e['api.worksheetName'] = this.get_name();
                    if (ss.isValue(this.get_parentDashboardImpl())) {
                        e['api.dashboardName'] = this.get_parentDashboardImpl().get_name()
                    }
                }
            }, get__filters: function () {
                return this.$H
            }, set__filters: function (e) {
                this.$H = e
            }, $s: function (e, cf, cg) {
                if (!K.isNullOrEmpty(e) && !K.isNullOrEmpty(cf)) {
                    throw J.createInternalError('Only fieldName OR fieldCaption is allowed, not both.')
                }
                cg = cg || new Object;
                var ch = new tab._Deferred;
                var ci = {};
                this.$d(ci);
                if (!K.isNullOrEmpty(cf) && K.isNullOrEmpty(e)) {
                    ci['api.fieldCaption'] = cf
                }
                if (!K.isNullOrEmpty(e)) {
                    ci['api.fieldName'] = e
                }
                ci['api.filterHierarchicalLevels'] = 0;
                ci['api.ignoreDomain'] = cg.ignoreDomain || false;
                var cj = new (ss.makeGenericType(bh, [Object]))('api.GetOneFilterInfoCommand', 0, ss.mkdel(this, function (ck) {
                    var cl = O.$2(ck);
                    if (ss.isNullOrUndefined(cl)) {
                        var cm = ck;
                        var cn = bO.$0(this, cm);
                        ch.resolve(cn)
                    } else {
                        ch.reject(cl)
                    }
                }), function (ck, cl) {
                    ch.reject(J.createServerError(cl))
                });
                this.sendCommand(Object).call(this, ci, cj);
                return ch.get_promise()
            }, $t: function (e) {
                this.$G();
                e = e || new Object;
                var cf = new tab._Deferred;
                var cg = {};
                this.$d(cg);
                cg['api.ignoreDomain'] = e.ignoreDomain || false;
                var ch = new (ss.makeGenericType(bh, [Object]))('api.GetFiltersListCommand', 0, ss.mkdel(this, function (ci) {
                    this.set__filters(bO.processFiltersList(this, ci));
                    cf.resolve(this.get__filters()._toApiCollection())
                }), function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $e: function (e, cf, cg, ch) {
                return this.$f(e, cf, cg, ch)
            }, $m: function (e) {
                return this.$n(e)
            }, $i: function (e, cf) {
                var cg = O.$3(cf);
                return this.$j(e, cg)
            }, $k: function (e, cf) {
                var cg = O.$4(cf);
                return this.$l(e, cg)
            }, $g: function (e, cf, cg, ch) {
                if (ss.isNullOrUndefined(cf) && cg !== 'all') {
                    throw J.createInvalidParameter('values')
                }
                return this.$h(e, cf, cg, ch)
            }, $n: function (e) {
                this.$G();
                if (K.isNullOrEmpty(e)) {
                    throw J.createNullOrEmptyParameter('fieldName')
                }
                var cf = new tab._Deferred;
                var cg = {};
                cg['api.fieldCaption'] = e;
                this.$d(cg);
                var ch = O.$0('api.ClearFilterCommand', e, cf);
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $f: function (e, cf, cg, ch) {
                this.$G();
                if (K.isNullOrEmpty(e)) {
                    throw J.createNullOrEmptyParameter('fieldName')
                }
                cg = n.$1(X).call(null, cg, 'updateType');
                var ci = [];
                if (A.isArray(cf)) {
                    for (var cj = 0; cj < cf.length; cj++) {
                        ci.push(cf[cj].toString())
                    }
                } else if (ss.isValue(cf)) {
                    ci.push(cf.toString())
                }
                var ck = new tab._Deferred;
                var cl = {};
                cl['api.fieldCaption'] = e;
                cl['api.filterUpdateType'] = cg;
                cl['api.exclude'] = ((ss.isValue(ch) && ch.isExcludeMode) ? true : false);
                if (cg !== 'all') {
                    cl['api.filterCategoricalValues'] = ci
                }
                this.$d(cl);
                var cm = O.$0('api.ApplyCategoricalFilterCommand', e, ck);
                this.sendCommand(Object).call(this, cl, cm);
                return ck.get_promise()
            }, $j: function (e, cf) {
                this.$G();
                if (K.isNullOrEmpty(e)) {
                    throw J.createNullOrEmptyParameter('fieldName')
                }
                if (ss.isNullOrUndefined(cf)) {
                    throw J.createNullOrEmptyParameter('filterOptions')
                }
                var cg = {};
                cg['api.fieldCaption'] = e;
                if (ss.isValue(cf.min)) {
                    if (K.isDate(cf.min)) {
                        var ch = cf.min;
                        if (K.isDateValid(ch)) {
                            cg['api.filterRangeMin'] = K.serializeDateForServer(ch)
                        } else {
                            throw J.createInvalidDateParameter('filterOptions.min')
                        }
                    } else {
                        cg['api.filterRangeMin'] = cf.min
                    }
                }
                if (ss.isValue(cf.max)) {
                    if (K.isDate(cf.max)) {
                        var ci = cf.max;
                        if (K.isDateValid(ci)) {
                            cg['api.filterRangeMax'] = K.serializeDateForServer(ci)
                        } else {
                            throw J.createInvalidDateParameter('filterOptions.max')
                        }
                    } else {
                        cg['api.filterRangeMax'] = cf.max
                    }
                }
                if (ss.isValue(cf.nullOption)) {
                    cg['api.filterRangeNullOption'] = cf.nullOption
                }
                this.$d(cg);
                var cj = new tab._Deferred;
                var ck = O.$0('api.ApplyRangeFilterCommand', e, cj);
                this.sendCommand(Object).call(this, cg, ck);
                return cj.get_promise()
            }, $l: function (e, cf) {
                this.$G();
                if (K.isNullOrEmpty(e)) {
                    throw J.createInvalidParameter('fieldName')
                } else if (ss.isNullOrUndefined(cf)) {
                    throw J.createInvalidParameter('filterOptions')
                }
                var cg = {};
                cg['api.fieldCaption'] = e;
                if (ss.isValue(cf)) {
                    cg['api.filterPeriodType'] = cf.periodType;
                    cg['api.filterDateRangeType'] = cf.rangeType;
                    if (cf.rangeType === 'lastn' || cf.rangeType === 'nextn') {
                        if (ss.isNullOrUndefined(cf.rangeN)) {
                            throw J.create('missingRangeNForRelativeDateFilters', 'Missing rangeN field for a relative date filter of LASTN or NEXTN.')
                        }
                        cg['api.filterDateRange'] = cf.rangeN
                    }
                    if (ss.isValue(cf.anchorDate)) {
                        cg['api.filterDateArchorValue'] = K.serializeDateForServer(cf.anchorDate)
                    }
                }
                this.$d(cg);
                var ch = new tab._Deferred;
                var ci = O.$0('api.ApplyRelativeDateFilterCommand', e, ch);
                this.sendCommand(Object).call(this, cg, ci);
                return ch.get_promise()
            }, $h: function (e, cf, cg, ch) {
                this.$G();
                if (K.isNullOrEmpty(e)) {
                    throw J.createNullOrEmptyParameter('fieldName')
                }
                cg = n.$1(X).call(null, cg, 'updateType');
                var ci = null;
                var cj = null;
                if (A.isArray(cf)) {
                    ci = [];
                    var ck = cf;
                    for (var cl = 0; cl < ck.length; cl++) {
                        ci.push(ck[cl].toString())
                    }
                } else if (K.isString(cf)) {
                    ci = [];
                    ci.push(cf.toString())
                } else if (ss.isValue(cf) && ss.isValue(cf['levels'])) {
                    var cm = cf['levels'];
                    cj = [];
                    if (A.isArray(cm)) {
                        var cn = cm;
                        for (var co = 0; co < cn.length; co++) {
                            cj.push(cn[co].toString())
                        }
                    } else {
                        cj.push(cm.toString())
                    }
                } else if (ss.isValue(cf)) {
                    throw J.createInvalidParameter('values')
                }
                var cp = {};
                cp['api.fieldCaption'] = e;
                cp['api.filterUpdateType'] = cg;
                cp['api.exclude'] = ((ss.isValue(ch) && ch.isExcludeMode) ? true : false);
                if (ss.isValue(ci)) {
                    cp['api.filterHierarchicalValues'] = JSON.stringify(ci)
                }
                if (ss.isValue(cj)) {
                    cp['api.filterHierarchicalLevels'] = JSON.stringify(cj)
                }
                this.$d(cp);
                var cq = new tab._Deferred;
                var cr = O.$0('api.ApplyHierarchicalFilterCommand', e, cq);
                this.sendCommand(Object).call(this, cp, cr);
                return cq.get_promise()
            }, get_selectedMarks: function () {
                return this.$J
            }, set_selectedMarks: function (e) {
                this.$J = e
            }, $p: function () {
                this.$G();
                var e = new tab._Deferred;
                var cf = {};
                this.$d(cf);
                var cg = new (ss.makeGenericType(bh, [Object]))('api.ClearSelectedMarksCommand', 1, function (ch) {
                    e.resolve()
                }, function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.sendCommand(Object).call(this, cf, cg);
                return e.get_promise()
            }, $B: function (e, cf, cg) {
                this.$G();
                if (ss.isNullOrUndefined(e) && ss.isNullOrUndefined(cf)) {
                    return this.$p()
                }
                if (K.isString(e) && (A.isArray(cf) || K.isString(cf) || !n.$0(bc).call(null, cf))) {
                    return this.$C(e, cf, cg)
                } else if (A.isArray(e)) {
                    return this.$D(e, cf)
                } else {
                    return this.$E(e, cf)
                }
            }, $v: function () {
                this.$G();
                var e = new tab._Deferred;
                var cf = {};
                this.$d(cf);
                var cg = new (ss.makeGenericType(bh, [Object]))('api.FetchSelectedMarksCommand', 0, ss.mkdel(this, function (ch) {
                    this.$J = l.$0(ch);
                    e.resolve(this.$J._toApiCollection())
                }), function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.sendCommand(Object).call(this, cf, cg);
                return e.get_promise()
            }, $C: function (e, cf, cg) {
                var ch = [];
                var ci = [];
                var cj = [];
                var ck = [];
                var cl = [];
                var cm = [];
                this.$A(ch, ci, cj, ck, cl, cm, e, cf);
                return this.$F(null, ch, ci, cj, ck, cl, cm, cg)
            }, $E: function (e, cf) {
                var cg = e;
                var ch = [];
                var ci = [];
                var cj = [];
                var ck = [];
                var cl = [];
                var cm = [];
                var cn = new ss.ObjectEnumerator(cg);
                try {
                    while (cn.moveNext()) {
                        var co = cn.current();
                        if (e.hasOwnProperty(co.key)) {
                            if (!A.isFunction(cg[co.key])) {
                                this.$A(ch, ci, cj, ck, cl, cm, co.key, co.value)
                            }
                        }
                    }
                } finally {
                    cn.dispose()
                }
                return this.$F(null, ch, ci, cj, ck, cl, cm, cf)
            }, $D: function (e, cf) {
                var cg = [];
                var ch = [];
                var ci = [];
                var cj = [];
                var ck = [];
                var cl = [];
                var cm = [];
                for (var cn = 0; cn < e.length; cn++) {
                    var co = e[cn];
                    if (ss.isValue(co.$0.$3()) && co.$0.$3() > 0) {
                        cm.push(co.$0.$3())
                    } else {
                        var cp = co.$0.$2();
                        for (var cq = 0; cq < cp.get__length(); cq++) {
                            var cr = cp.get_item(cq);
                            if (cr.hasOwnProperty('fieldName') && cr.hasOwnProperty('value') && !A.isFunction(cr.fieldName) && !A.isFunction(cr.value)) {
                                this.$A(cg, ch, ci, cj, ck, cl, cr.fieldName, cr.value)
                            }
                        }
                    }
                }
                return this.$F(cm, cg, ch, ci, cj, ck, cl, cf)
            }, $A: function (e, cf, cg, ch, ci, cj, ck, cl) {
                var cm = cl;
                if (O.$5.test(ck)) {
                    this.$c(cg, ch, ck, cl)
                } else if (ss.isValue(cm.min) || ss.isValue(cm.max)) {
                    var cn = new Object;
                    if (ss.isValue(cm.min)) {
                        if (K.isDate(cm.min)) {
                            var co = cm.min;
                            if (K.isDateValid(co)) {
                                cn.min = K.serializeDateForServer(co)
                            } else {
                                throw J.createInvalidDateParameter('options.min')
                            }
                        } else {
                            cn.min = cm.min
                        }
                    }
                    if (ss.isValue(cm.max)) {
                        if (K.isDate(cm.max)) {
                            var cp = cm.max;
                            if (K.isDateValid(cp)) {
                                cn.max = K.serializeDateForServer(cp)
                            } else {
                                throw J.createInvalidDateParameter('options.max')
                            }
                        } else {
                            cn.max = cm.max
                        }
                    }
                    if (ss.isValue(cm.nullOption)) {
                        var cq = n.$1(Y).call(null, cm.nullOption, 'options.nullOption');
                        cn.nullOption = cq
                    } else {
                        cn.nullOption = 'allValues'
                    }
                    var cr = JSON.stringify(cn);
                    this.$c(ci, cj, ck, cr)
                } else {
                    this.$c(e, cf, ck, cl)
                }
            }, $c: function (e, cf, cg, ch) {
                var ci = [];
                if (A.isArray(ch)) {
                    var cj = ch;
                    for (var ck = 0; ck < cj.length; ck++) {
                        ci.push(cj[ck].toString())
                    }
                } else {
                    ci.push(ch.toString())
                }
                cf.push(ci);
                e.push(cg)
            }, $F: function (e, cf, cg, ch, ci, cj, ck, cl) {
                var cm = {};
                this.$d(cm);
                cl = n.$1(bc).call(null, cl, 'updateType');
                cm['api.filterUpdateType'] = cl;
                if (!K.isNullOrEmpty(e)) {
                    cm['api.tupleIds'] = JSON.stringify(e)
                }
                if (!K.isNullOrEmpty(cf) && !K.isNullOrEmpty(cg)) {
                    cm['api.categoricalFieldCaption'] = JSON.stringify(cf);
                    var cn = [];
                    for (var co = 0; co < cg.length; co++) {
                        var cp = JSON.stringify(cg[co]);
                        cn.push(cp)
                    }
                    cm['api.categoricalMarkValues'] = JSON.stringify(cn)
                }
                if (!K.isNullOrEmpty(ch) && !K.isNullOrEmpty(ci)) {
                    cm['api.hierarchicalFieldCaption'] = JSON.stringify(ch);
                    var cq = [];
                    for (var cr = 0; cr < ci.length; cr++) {
                        var cs = JSON.stringify(ci[cr]);
                        cq.push(cs)
                    }
                    cm['api.hierarchicalMarkValues'] = JSON.stringify(cq)
                }
                if (!K.isNullOrEmpty(cj) && !K.isNullOrEmpty(ck)) {
                    cm['api.rangeFieldCaption'] = JSON.stringify(cj);
                    var ct = [];
                    for (var cu = 0; cu < ck.length; cu++) {
                        var cv = JSON.stringify(ck[cu]);
                        ct.push(cv)
                    }
                    cm['api.rangeMarkValues'] = JSON.stringify(ct)
                }
                if (K.isNullOrEmpty(cm['api.tupleIds']) && K.isNullOrEmpty(cm['api.categoricalFieldCaption']) && K.isNullOrEmpty(cm['api.hierarchicalFieldCaption']) && K.isNullOrEmpty(cm['api.rangeFieldCaption'])) {
                    throw J.createInvalidParameter('fieldNameOrFieldValuesMap')
                }
                var cw = new tab._Deferred;
                var cx = new (ss.makeGenericType(bh, [Object]))('api.SelectMarksCommand', 1, function (cy) {
                    var cz = O.$1(cy);
                    if (ss.isNullOrUndefined(cz)) {
                        cw.resolve()
                    } else {
                        cw.reject(cz)
                    }
                }, function (cy, cz) {
                    cw.reject(J.createServerError(cz))
                });
                this.sendCommand(Object).call(this, cm, cx);
                return cw.get_promise()
            }, $w: function (e) {
                this.$G();
                var cf = new tab._Deferred;
                var cg = {};
                this.$d(cg);
                e = e || new Object;
                cg['api.ignoreAliases'] = ss.coalesce(e.ignoreAliases, false);
                cg['api.ignoreSelection'] = ss.coalesce(e.ignoreSelection, false);
                cg['api.maxRows'] = ss.coalesce(e.maxRows, 0);
                var ch = new (ss.makeGenericType(bh, [Object]))('api.GetSummaryTableCommand', 0, function (ci) {
                    var cj = ci;
                    var ck = y.processGetDataPresModel(cj);
                    cf.resolve(ck)
                }, function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $x: function (e) {
                this.$G();
                var cf = new tab._Deferred;
                var cg = {};
                this.$d(cg);
                e = e || new Object;
                cg['api.ignoreAliases'] = ss.coalesce(e.ignoreAliases, false);
                cg['api.ignoreSelection'] = ss.coalesce(e.ignoreSelection, false);
                cg['api.includeAllColumns'] = ss.coalesce(e.includeAllColumns, false);
                cg['api.maxRows'] = ss.coalesce(e.maxRows, 0);
                var ch = new (ss.makeGenericType(bh, [Object]))('api.GetUnderlyingTableCommand', 0, function (ci) {
                    var cj = ci;
                    var ck = y.processGetDataPresModel(cj);
                    cf.resolve(ck)
                }, function (ci, cj) {
                    cf.reject(J.createServerError(cj))
                });
                this.sendCommand(Object).call(this, cg, ch);
                return cf.get_promise()
            }, $o: function () {
                this.$G();
                var e = new tab._Deferred;
                var cf = {};
                this.$d(cf);
                var cg = new (ss.makeGenericType(bh, [Object]))('api.ClearHighlightedMarksCommand', 1, function (ch) {
                    e.resolve()
                }, function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.sendCommand(Object).call(this, cf, cg);
                return e.get_promise()
            }, $y: function (e, cf) {
                B.verifyString(e, 'fieldName');
                this.$G();
                var cg = new tab._Deferred;
                var ch = {};
                ch['api.fieldCaption'] = e;
                ch['api.ObjectTextIDs'] = cf;
                this.$d(ch);
                var ci = new (ss.makeGenericType(bh, [Object]))('api.HighlightMarksCommand', 0, function (cj) {
                    cg.resolve()
                }, function (cj, ck) {
                    cg.reject(J.createServerError(ck))
                });
                this.sendCommand(Object).call(this, ch, ci);
                return cg.get_promise()
            }, $z: function (e, cf) {
                B.verifyString(e, 'fieldName');
                B.verifyString(cf, 'patternMatch');
                this.$G();
                var cg = new tab._Deferred;
                var ch = {};
                ch['api.filterUpdateType'] = 'replace';
                ch['api.fieldCaption'] = e;
                ch['api.Pattern'] = cf;
                this.$d(ch);
                var ci = new (ss.makeGenericType(bh, [Object]))('api.HighlightMarksByPatternMatch', 0, function (cj) {
                    cg.resolve()
                }, function (cj, ck) {
                    cg.reject(J.createServerError(ck))
                });
                this.sendCommand(Object).call(this, ch, ci);
                return cg.get_promise()
            }, $u: function () {
                this.$G();
                var e = new tab._Deferred;
                var cf = {};
                this.$d(cf);
                var cg = new (ss.makeGenericType(bh, [Object]))('api.FetchHighlightedMarksCommand', 0, ss.mkdel(this, function (ch) {
                    this.highlightedMarks = l.$0(ch);
                    e.resolve(this.highlightedMarks._toApiCollection())
                }), function (ch, ci) {
                    e.reject(J.createServerError(ci))
                });
                this.sendCommand(Object).call(this, cf, cg);
                return e.get_promise()
            }
        }, E);
        ss.initEnum(P, a, {
            blank: 'blank',
            worksheet: 'worksheet',
            quickFilter: 'quickFilter',
            parameterControl: 'parameterControl',
            pageFilter: 'pageFilter',
            legend: 'legend',
            title: 'title',
            text: 'text',
            image: 'image',
            webPage: 'webPage'
        }, true);
        ss.initEnum(Q, a, {last: 'last', lastn: 'lastn', next: 'next', nextn: 'nextn', curr: 'curr', todate: 'todate'}, true);
        ss.initEnum(R, a, {default: 'default', desktop: 'desktop', tablet: 'tablet', phone: 'phone'}, true);
        ss.initClass(S, a, {});
        ss.initEnum(T, a, {
            internalError: 'internalError',
            serverError: 'serverError',
            invalidAggregationFieldName: 'invalidAggregationFieldName',
            invalidParameter: 'invalidParameter',
            invalidUrl: 'invalidUrl',
            staleDataReference: 'staleDataReference',
            vizAlreadyInManager: 'vizAlreadyInManager',
            noUrlOrParentElementNotFound: 'noUrlOrParentElementNotFound',
            invalidFilterFieldName: 'invalidFilterFieldName',
            invalidFilterFieldValue: 'invalidFilterFieldValue',
            invalidFilterFieldNameOrValue: 'invalidFilterFieldNameOrValue',
            filterCannotBePerformed: 'filterCannotBePerformed',
            notActiveSheet: 'notActiveSheet',
            invalidCustomViewName: 'invalidCustomViewName',
            missingRangeNForRelativeDateFilters: 'missingRangeNForRelativeDateFilters',
            missingMaxSize: 'missingMaxSize',
            missingMinSize: 'missingMinSize',
            missingMinMaxSize: 'missingMinMaxSize',
            invalidSize: 'invalidSize',
            invalidSizeBehaviorOnWorksheet: 'invalidSizeBehaviorOnWorksheet',
            sheetNotInWorkbook: 'sheetNotInWorkbook',
            indexOutOfRange: 'indexOutOfRange',
            downloadWorkbookNotAllowed: 'downloadWorkbookNotAllowed',
            nullOrEmptyParameter: 'nullOrEmptyParameter',
            browserNotCapable: 'browserNotCapable',
            unsupportedEventName: 'unsupportedEventName',
            invalidDateParameter: 'invalidDateParameter',
            invalidSelectionFieldName: 'invalidSelectionFieldName',
            invalidSelectionValue: 'invalidSelectionValue',
            invalidSelectionDate: 'invalidSelectionDate',
            noUrlForHiddenWorksheet: 'noUrlForHiddenWorksheet',
            maxVizResizeAttempts: 'maxVizResizeAttempts'
        }, true);
        ss.initEnum(U, a, {
            SUM: 'SUM',
            AVG: 'AVG',
            MIN: 'MIN',
            MAX: 'MAX',
            STDEV: 'STDEV',
            STDEVP: 'STDEVP',
            VAR: 'VAR',
            VARP: 'VARP',
            COUNT: 'COUNT',
            COUNTD: 'COUNTD',
            MEDIAN: 'MEDIAN',
            ATTR: 'ATTR',
            NONE: 'NONE',
            PERCENTILE: 'PERCENTILE',
            YEAR: 'YEAR',
            QTR: 'QTR',
            MONTH: 'MONTH',
            DAY: 'DAY',
            HOUR: 'HOUR',
            MINUTE: 'MINUTE',
            SECOND: 'SECOND',
            WEEK: 'WEEK',
            WEEKDAY: 'WEEKDAY',
            MONTHYEAR: 'MONTHYEAR',
            MDY: 'MDY',
            END: 'END',
            TRUNC_YEAR: 'TRUNC_YEAR',
            TRUNC_QTR: 'TRUNC_QTR',
            TRUNC_MONTH: 'TRUNC_MONTH',
            TRUNC_WEEK: 'TRUNC_WEEK',
            TRUNC_DAY: 'TRUNC_DAY',
            TRUNC_HOUR: 'TRUNC_HOUR',
            TRUNC_MINUTE: 'TRUNC_MINUTE',
            TRUNC_SECOND: 'TRUNC_SECOND',
            QUART1: 'QUART1',
            QUART3: 'QUART3',
            SKEWNESS: 'SKEWNESS',
            KURTOSIS: 'KURTOSIS',
            INOUT: 'INOUT',
            SUM_XSQR: 'SUM_XSQR',
            USER: 'USER'
        }, true);
        ss.initEnum(V, a, {dimension: 'dimension', measure: 'measure', unknown: 'unknown'}, true);
        ss.initEnum(W, a, {categorical: 'categorical', quantitative: 'quantitative', hierarchical: 'hierarchical', relativedate: 'relativedate'}, true);
        ss.initEnum(X, a, {all: 'all', replace: 'replace', add: 'add', remove: 'remove'}, true);
        ss.initEnum(Y, a, {nullValues: 'nullValues', nonNullValues: 'nonNullValues', allValues: 'allValues'}, true);
        ss.initEnum(Z, a, {all: 'all', list: 'list', range: 'range'}, true);
        ss.initEnum(ba, a, {float: 'float', integer: 'integer', string: 'string', boolean: 'boolean', date: 'date', datetime: 'datetime'}, true);
        ss.initEnum(bb, a, {year: 'year', quarter: 'quarter', month: 'month', week: 'week', day: 'day', hour: 'hour', minute: 'minute', second: 'second'}, true);
        ss.initEnum(bc, a, {replace: 'replace', add: 'add', remove: 'remove'}, true);
        ss.initEnum(bd, a, {automatic: 'automatic', exactly: 'exactly', range: 'range', atleast: 'atleast', atmost: 'atmost'}, true);
        ss.initEnum(be, a, {worksheet: 'worksheet', dashboard: 'dashboard', story: 'story'}, true);
        ss.initEnum(bf, a, {
            customviewload: 'customviewload',
            customviewremove: 'customviewremove',
            customviewsave: 'customviewsave',
            customviewsetdefault: 'customviewsetdefault',
            filterchange: 'filterchange',
            firstinteractive: 'firstinteractive',
            firstvizsizeknown: 'firstvizsizeknown',
            marksselection: 'marksselection',
            markshighlight: 'markshighlight',
            parametervaluechange: 'parametervaluechange',
            storypointswitch: 'storypointswitch',
            tabswitch: 'tabswitch',
            vizresize: 'vizresize'
        }, true);
        ss.initEnum(bg, a, {top: 'top', bottom: 'bottom'}, true);
        ss.initClass(bi, a, {
            get_router: function () {
                return this.$1
            }, get_handler: function () {
                return this.$0
            }, sendCommand: function (e) {
                return function (cf, cg) {
                    this.$1.sendCommand(e).call(this.$1, this.$0, cf, cg)
                }
            }
        });
        ss.initClass(bA, a, {
            getViz: function () {
                return this.$1
            }, getEventName: function () {
                return this.$0
            }
        });
        ss.initClass(bj, a, {
            getCustomViewAsync: function () {
                var e = new tab._Deferred;
                var cf = null;
                if (ss.isValue(this.$2.get__customViewImpl())) {
                    cf = this.$2.get__customViewImpl().$5()
                }
                e.resolve(cf);
                return e.get_promise()
            }
        }, bA);
        ss.initEnum(bk, a, {float: 'float', integer: 'integer', string: 'string', boolean: 'boolean', date: 'date', datetime: 'datetime'}, true);
        ss.initClass(bl, a, {}, Object);
        ss.initClass(bF, a, {
            getWorksheet: function () {
                return this.$2.get_worksheet()
            }
        }, bA);
        ss.initClass(bn, a, {
            getFieldName: function () {
                return this.$4
            }, getFilterAsync: function () {
                return this.$3.get__worksheetImpl().$s(this.$3.get__filterFieldName(), null, null)
            }
        }, bF);
        ss.initClass(bo, a, {
            getVizSize: function () {
                return this.$2
            }
        }, bA);
        ss.initClass(bp, a, {
            getHighlightedMarksAsync: function () {
                var e = this.$3.get__worksheetImpl();
                return e.$u()
            }
        }, bF);
        ss.initClass(bs, a, {
            getMarksAsync: function () {
                var e = this.$3.get__worksheetImpl();
                if (ss.isValue(e.get_selectedMarks())) {
                    var cf = new tab._Deferred;
                    return cf.resolve(e.get_selectedMarks()._toApiCollection())
                }
                return e.$v()
            }
        }, bF);
        ss.initClass(bt, a, {
            getParameterName: function () {
                return this.$2.get__parameterName()
            }, getParameterAsync: function () {
                return this.$2.get__workbookImpl().$8(this.$2.get__parameterName())
            }
        }, bA);
        ss.initClass(bu, a, {}, Object);
        ss.initClass(bv, a, {}, Object);
        ss.initClass(bw, a, {});
        ss.initClass(bx, a, {}, Object);
        ss.initClass(by, a, {});
        ss.initClass(bz, a, {
            getOldStoryPointInfo: function () {
                return this.$3
            }, getNewStoryPoint: function () {
                return this.$2
            }
        }, bA);
        ss.initClass(bB, a, {
            getOldSheetName: function () {
                return this.$3
            }, getNewSheetName: function () {
                return this.$2
            }
        }, bA);
        ss.initClass(bC, a, {
            add_customViewsListLoad: function (e) {
                this.$1$1 = ss.delegateCombine(this.$1$1, e)
            }, remove_customViewsListLoad: function (e) {
                this.$1$1 = ss.delegateRemove(this.$1$1, e)
            }, add_stateReadyForQuery: function (e) {
                this.$1$2 = ss.delegateCombine(this.$1$2, e)
            }, remove_stateReadyForQuery: function (e) {
                this.$1$2 = ss.delegateRemove(this.$1$2, e)
            }, $1C: function (e) {
                this.$1$3 = ss.delegateCombine(this.$1$3, e)
            }, $1D: function (e) {
                this.$1$3 = ss.delegateRemove(this.$1$3, e)
            }, $1A: function (e) {
                this.$1$4 = ss.delegateCombine(this.$1$4, e)
            }, $1B: function (e) {
                this.$1$4 = ss.delegateRemove(this.$1$4, e)
            }, $1y: function (e) {
                this.$1$5 = ss.delegateCombine(this.$1$5, e)
            }, $1z: function (e) {
                this.$1$5 = ss.delegateRemove(this.$1$5, e)
            }, $1E: function (e) {
                this.$1$6 = ss.delegateCombine(this.$1$6, e)
            }, $1F: function (e) {
                this.$1$6 = ss.delegateRemove(this.$1$6, e)
            }, $1q: function (e) {
                this.$1$7 = ss.delegateCombine(this.$1$7, e)
            }, $1r: function (e) {
                this.$1$7 = ss.delegateRemove(this.$1$7, e)
            }, $1u: function (e) {
                this.$1$8 = ss.delegateCombine(this.$1$8, e)
            }, $1v: function (e) {
                this.$1$8 = ss.delegateRemove(this.$1$8, e)
            }, $1s: function (e) {
                this.$1$9 = ss.delegateCombine(this.$1$9, e)
            }, $1t: function (e) {
                this.$1$9 = ss.delegateRemove(this.$1$9, e)
            }, $1w: function (e) {
                this.$1$10 = ss.delegateCombine(this.$1$10, e)
            }, $1x: function (e) {
                this.$1$10 = ss.delegateRemove(this.$1$10, e)
            }, $1I: function (e) {
                this.$1$11 = ss.delegateCombine(this.$1$11, e)
            }, $1J: function (e) {
                this.$1$11 = ss.delegateRemove(this.$1$11, e)
            }, $1G: function (e) {
                this.$1$12 = ss.delegateCombine(this.$1$12, e)
            }, $1H: function (e) {
                this.$1$12 = ss.delegateRemove(this.$1$12, e)
            }, $1K: function (e) {
                this.$1$13 = ss.delegateCombine(this.$1$13, e)
            }, $1L: function (e) {
                this.$1$13 = ss.delegateRemove(this.$1$13, e)
            }, get_hostId: function () {
                return this.$1k.hostId
            }, set_hostId: function (e) {
                this.$1k.hostId = e
            }, get_iframe: function () {
                return this.$1b
            }, get_instanceId: function () {
                return this.$1e
            }, set_instanceId: function (e) {
                this.$1e = e
            }, $15: function () {
                return this.$1m
            }, $10: function () {
                return this.$1a
            }, $12: function () {
                return this.$1f
            }, $11: function () {
                return this.$1b.style.display === 'none'
            }, $13: function () {
                return this.$1k.parentElement
            }, $14: function () {
                return this.$1k.get_baseUrl()
            }, $17: function () {
                return this.$1p.get_workbook()
            }, get__workbookImpl: function () {
                return this.$1p
            }, $Z: function () {
                return this.$19
            }, $16: function () {
                return this.$1n
            }, getCurrentUrlAsync: function () {
                var e = new tab._Deferred;
                var cf = new (ss.makeGenericType(bh, [String]))('api.GetCurrentUrlCommand', 0, function (cg) {
                    e.resolve(cg)
                }, function (cg, ch) {
                    e.reject(J.createInternalError(ch))
                });
                this._sendCommand(String).call(this, null, cf);
                return e.get_promise()
            }, handleVizListening: function () {
                this.$8()
            }, handleVizLoad: function () {
                if (ss.isNullOrUndefined(this.$1n)) {
                    this.$O(this.$1c.width + 'px', this.$1c.height + 'px');
                    this.$Q()
                }
                if (ss.isValue(this.$1l)) {
                    this.$1l.style.display = 'none'
                }
                if (ss.isNullOrUndefined(this.$1p)) {
                    this.$1p = new N(this, this.$1g, ss.mkdel(this, function () {
                        this.$w(null)
                    }))
                } else if (!this.$1d) {
                    this.$1p._update(ss.mkdel(this, function () {
                        this.$w(null)
                    }))
                }
            }, $1: function (e) {
                var cf = this.$1n.chromeHeight;
                var cg = this.$1n.sheetSize;
                var ch = 0;
                var ci = 0;
                if (cg.behavior === 'exactly') {
                    ch = cg.maxSize.width;
                    ci = cg.maxSize.height + cf
                } else {
                    var cj;
                    var ck;
                    var cl;
                    var cm;
                    switch (cg.behavior) {
                        case'range': {
                            cj = cg.minSize.width;
                            ck = cg.maxSize.width;
                            cl = cg.minSize.height + cf;
                            cm = cg.maxSize.height + cf;
                            ch = Math.max(cj, Math.min(ck, e.width));
                            ci = Math.max(cl, Math.min(cm, e.height));
                            break
                        }
                        case'atleast': {
                            cj = cg.minSize.width;
                            cl = cg.minSize.height + cf;
                            ch = Math.max(cj, e.width);
                            ci = Math.max(cl, e.height);
                            break
                        }
                        case'atmost': {
                            ck = cg.maxSize.width;
                            cm = cg.maxSize.height + cf;
                            ch = Math.min(ck, e.width);
                            ci = Math.min(cm, e.height);
                            break
                        }
                        case'automatic': {
                            ch = e.width;
                            ci = Math.max(e.height, cf);
                            break
                        }
                        default: {
                            throw J.createInternalError('Unknown SheetSizeBehavior for viz: ' + cg.behavior.toString())
                        }
                    }
                }
                return bx.$ctor(ch, ci)
            }, $b: function () {
                var e;
                if (ss.isValue(this.$1c)) {
                    e = this.$1c;
                    this.$1c = null
                } else {
                    e = K.computeContentSize(this.$13())
                }
                this.$G(e);
                return this.$1(e)
            }, $I: function () {
                if (!ss.isValue(this.$1n)) {
                    return
                }
                var e = this.$b();
                if (e.height === this.$1n.chromeHeight) {
                    return
                }
                this.$O(e.width + 'px', e.height + 'px');
                var cf = 10;
                for (var cg = 0; cg < cf; cg++) {
                    var ch = this.$b();
                    if (ss.referenceEquals(JSON.stringify(e), JSON.stringify(ch))) {
                        return
                    }
                    e = ch;
                    this.$O(e.width + 'px', e.height + 'px')
                }
                throw J.create('maxVizResizeAttempts', 'Viz resize limit hit. The calculated iframe size did not stabilize after ' + cf + ' resizes.')
            }, handleEventNotification: function (e, cf) {
                var cg = r.deserialize(cf);
                switch (e) {
                    case'api.FirstVizSizeKnownEvent': {
                        this.$i(cg);
                        break
                    }
                    case'api.VizInteractiveEvent': {
                        this.$p(cg);
                        break
                    }
                    case'api.MarksSelectionChangedEvent': {
                        this.$l(cg);
                        break
                    }
                    case'api.MarksHighlightChangedEvent': {
                        this.$k(cg);
                        break
                    }
                    case'api.FilterChangedEvent': {
                        this.$h(cg);
                        break
                    }
                    case'api.ParameterChangedEvent': {
                        this.$m(cg);
                        break
                    }
                    case'api.CustomViewsListLoadedEvent': {
                        this.$g(cg);
                        break
                    }
                    case'api.CustomViewUpdatedEvent': {
                        this.$f(cg);
                        break
                    }
                    case'api.CustomViewRemovedEvent': {
                        this.$d();
                        break
                    }
                    case'api.CustomViewSetDefaultEvent': {
                        this.$e(cg);
                        break
                    }
                    case'api.TabSwitchEvent': {
                        this.$o(cg);
                        break
                    }
                    case'api.StorytellingStateChangedEvent': {
                        this.$n(cg);
                        break
                    }
                }
            }, addEventListener: function (e, cf) {
                var cg = {};
                if (!n.$2(bf).call(null, e, cg)) {
                    throw J.createUnsupportedEventName(e.toString())
                }
                switch (cg.$) {
                    case'marksselection': {
                        this.$1C(cf);
                        break
                    }
                    case'markshighlight': {
                        this.$1A(cf);
                        break
                    }
                    case'parametervaluechange': {
                        this.$1E(cf);
                        break
                    }
                    case'filterchange': {
                        this.$1y(cf);
                        break
                    }
                    case'customviewload': {
                        this.$1q(cf);
                        break
                    }
                    case'customviewsave': {
                        this.$1u(cf);
                        break
                    }
                    case'customviewremove': {
                        this.$1s(cf);
                        break
                    }
                    case'customviewsetdefault': {
                        this.$1w(cf);
                        break
                    }
                    case'tabswitch': {
                        this.$1I(cf);
                        break
                    }
                    case'storypointswitch': {
                        this.$1G(cf);
                        break
                    }
                    case'vizresize': {
                        this.$1K(cf);
                        break
                    }
                }
            }, removeEventListener: function (e, cf) {
                var cg = {};
                if (!n.$2(bf).call(null, e, cg)) {
                    throw J.createUnsupportedEventName(e.toString())
                }
                switch (cg.$) {
                    case'marksselection': {
                        this.$1D(cf);
                        break
                    }
                    case'markshighlight': {
                        this.$1B(cf);
                        break
                    }
                    case'parametervaluechange': {
                        this.$1F(cf);
                        break
                    }
                    case'filterchange': {
                        this.$1z(cf);
                        break
                    }
                    case'customviewload': {
                        this.$1r(cf);
                        break
                    }
                    case'customviewsave': {
                        this.$1v(cf);
                        break
                    }
                    case'customviewremove': {
                        this.$1t(cf);
                        break
                    }
                    case'customviewsetdefault': {
                        this.$1x(cf);
                        break
                    }
                    case'tabswitch': {
                        this.$1J(cf);
                        break
                    }
                    case'storypointswitch': {
                        this.$1H(cf);
                        break
                    }
                    case'vizresize': {
                        this.$1L(cf);
                        break
                    }
                }
            }, $7: function () {
                if (ss.isValue(this.$1b)) {
                    this.$1b.parentNode.removeChild(this.$1b);
                    this.$1b = null
                }
                L.$2(this.$1m);
                this.$1g.get_router().unregisterHandler(this);
                this.$J()
            }, $Q: function () {
                this.$1b.style.display = 'block';
                this.$1b.style.visibility = 'visible'
            }, $q: function () {
                this.$1b.style.display = 'none'
            }, $t: function () {
                this.$1b.style.visibility = 'hidden'
            }, $U: function () {
                this.$s('showExportImageDialog')
            }, $T: function (e) {
                var cf = this.$Y(e);
                this.$s('showExportDataDialog', cf)
            }, $S: function (e) {
                var cf = this.$Y(e);
                this.$s('showExportCrosstabDialog', cf)
            }, $V: function () {
                this.$s('showExportPDFDialog')
            }, $L: function () {
                var e = new tab._Deferred;
                var cf = new (ss.makeGenericType(bh, [Object]))('api.RevertAllCommand', 1, function (cg) {
                    e.resolve()
                }, function (cg, ch) {
                    e.reject(J.createServerError(ch))
                });
                this._sendCommand(Object).call(this, null, cf);
                return e.get_promise()
            }, $H: function () {
                var e = new tab._Deferred;
                var cf = new (ss.makeGenericType(bh, [Object]))('api.RefreshDataCommand', 1, function (cg) {
                    e.resolve()
                }, function (cg, ch) {
                    e.reject(J.createServerError(ch))
                });
                this._sendCommand(Object).call(this, null, cf);
                return e.get_promise()
            }, $W: function () {
                this.$s('showShareDialog')
            }, $R: function () {
                if (this.get__workbookImpl().get_isDownloadAllowed()) {
                    this.$s('showDownloadWorkbookDialog')
                } else {
                    throw J.create('downloadWorkbookNotAllowed', 'Download workbook is not allowed')
                }
            }, $x: function () {
                return this.$r('pauseAutomaticUpdates')
            }, $K: function () {
                return this.$r('resumeAutomaticUpdates')
            }, $X: function () {
                return this.$r('toggleAutomaticUpdates')
            }, $P: function (e, cf) {
                this.$G(bx.$ctor(-1, -1));
                this.$O(e, cf);
                this.$1p._updateActiveSheetAsync()
            }, $N: function (e) {
                this.$19 = e
            }, $3: function () {
                return this.$1k.parentElement
            }, $4: function () {
                try {
                    L.$0(this.$1m)
                } catch (cf) {
                    var e = ss.Exception.wrap(cf);
                    this.$7();
                    throw e
                }
                if (!this.$1k.fixedSize) {
                    this.$1c = K.computeContentSize(this.$13());
                    if (this.$1c.width === 0 || this.$1c.height === 0) {
                        this.$1c = bx.$ctor(800, 600)
                    }
                    this.$1b = this.$5();
                    this.$t();
                    if (this.$1k.displayStaticImage) {
                        this.$1l = this.$6(this.$1c);
                        this.$1l.style.display = 'block'
                    }
                } else {
                    if (this.$1k.displayStaticImage) {
                        this.$1l = this.$6(bx.$ctor(parseInt(this.$1k.width), parseInt(this.$1k.height)));
                        this.$1l.style.display = 'block'
                    }
                    this.$1b = this.$5();
                    this.$Q()
                }
                if (!K.hasWindowPostMessage()) {
                    if (K.isIE()) {
                        this.$1b['onreadystatechange'] = this.$c()
                    } else {
                        this.$1b.onload = this.$c()
                    }
                }
                this.$1f = !this.$1k.toolbar;
                this.$1a = !this.$1k.tabs;
                this.$1g.get_router().registerHandler(this);
                this.$1b.src = this.$1k.get_url()
            }, $M: function () {
                try {
                    if (!K.hasWindowPostMessage() || ss.isNullOrUndefined(this.$1b) || !ss.isValue(this.$1b.contentWindow)) {
                        return
                    }
                } catch (ch) {
                    return
                }
                var e = K.visibleContentRectInDocumentCoordinates(this.get_iframe());
                var cf = K.contentRectInDocumentCoordinates(this.get_iframe());
                var cg = [];
                cg.push('layoutInfoResp'.toString());
                cg.push(e.left - cf.left);
                cg.push(e.top - cf.top);
                cg.push(e.width);
                cg.push(e.height);
                this.$1b.contentWindow.postMessage(cg.join(','), '*')
            }, $8: function () {
                if (!K.hasWindowPostMessage() || ss.isNullOrUndefined(this.$1b) || !ss.isValue(this.$1b.contentWindow)) {
                    return
                }
                this.$1b.contentWindow.postMessage('tableau.enableVisibleRectCommunication'.toString(), '*')
            }, _sendCommand: function (e) {
                return function (cf, cg) {
                    this.$1g.sendCommand(e).call(this.$1g, cf, cg)
                }
            }, $D: function (e) {
                if (!ss.staticEquals(this.$1$6, null)) {
                    this.$1$6(new bt('parametervaluechange', this.$1m, e))
                }
            }, $y: function (e) {
                this.get__workbookImpl()._update(ss.mkdel(this, function () {
                    if (!ss.staticEquals(this.$1$7, null)) {
                        this.$1$7(new bj('customviewload', this.$1m, (ss.isValue(e) ? e._impl : null)))
                    }
                }))
            }, $A: function (e) {
                this.get__workbookImpl()._update(ss.mkdel(this, function () {
                    if (!ss.staticEquals(this.$1$8, null)) {
                        this.$1$8(new bj('customviewsave', this.$1m, e._impl))
                    }
                }))
            }, $z: function (e) {
                if (!ss.staticEquals(this.$1$9, null)) {
                    this.$1$9(new bj('customviewremove', this.$1m, e._impl))
                }
            }, $B: function (e) {
                if (!ss.staticEquals(this.$1$10, null)) {
                    this.$1$10(new bj('customviewsetdefault', this.$1m, e._impl))
                }
            }, $F: function (e, cf) {
                if (!ss.staticEquals(this.$1$11, null)) {
                    this.$1$11(new bB('tabswitch', this.$1m, e, cf))
                }
            }, raiseStoryPointSwitch: function (e, cf) {
                if (!ss.staticEquals(this.$1$12, null)) {
                    this.$1$12(new bz('storypointswitch', this.$1m, e, cf))
                }
            }, $E: function () {
                if (!ss.staticEquals(this.$1$2, null)) {
                    this.$1$2(this)
                }
            }, $C: function () {
                if (!ss.staticEquals(this.$1$1, null)) {
                    this.$1$1(this)
                }
            }, $G: function (e) {
                if (!ss.staticEquals(this.$1$13, null)) {
                    this.$1$13(new bD('vizresize', this.$1m, e))
                }
            }, $O: function (e, cf) {
                this.$1k.width = e;
                this.$1k.height = cf;
                this.$1b.style.width = this.$1k.width;
                this.$1b.style.height = this.$1k.height
            }, $Y: function (e) {
                if (ss.isNullOrUndefined(e)) {
                    return null
                }
                var cf = this.$1p.$4(e);
                if (ss.isNullOrUndefined(cf)) {
                    throw J.createNotActiveSheet()
                }
                return cf.get_name()
            }, $r: function (e) {
                if (e !== 'pauseAutomaticUpdates' && e !== 'resumeAutomaticUpdates' && e !== 'toggleAutomaticUpdates') {
                    throw J.createInternalError(null)
                }
                var cf = {};
                cf['api.invokeCommandName'] = e;
                var cg = new tab._Deferred;
                var ch = new (ss.makeGenericType(bh, [Object]))('api.InvokeCommandCommand', 0, ss.mkdel(this, function (ci) {
                    if (ss.isValue(ci) && ss.isValue(ci.isAutoUpdate)) {
                        this.$19 = !ci.isAutoUpdate
                    }
                    cg.resolve(this.$19)
                }), function (ci, cj) {
                    cg.reject(J.createServerError(cj))
                });
                this._sendCommand(Object).call(this, cf, ch);
                return cg.get_promise()
            }, $s: function (e, cf) {
                if (e !== 'showExportImageDialog' && e !== 'showExportDataDialog' && e !== 'showExportCrosstabDialog' && e !== 'showExportPDFDialog' && e !== 'showShareDialog' && e !== 'showDownloadWorkbookDialog') {
                    throw J.createInternalError(null)
                }
                var cg = {};
                cg['api.invokeCommandName'] = e;
                if (ss.isValue(cf)) {
                    cg['api.invokeCommandParam'] = cf
                }
                var ch = new (ss.makeGenericType(bh, [Object]))('api.InvokeCommandCommand', 0, null, null);
                this._sendCommand(Object).call(this, cg, ch)
            }, $i: function (e) {
                var cf = JSON.parse(e.get_data());
                this.$j(cf)
            }, $p: function (e) {
                if (ss.isValue(this.$1p) && ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                    this.$w(null)
                } else {
                    this.$E()
                }
            }, $l: function (e) {
                if (ss.staticEquals(this.$1$3, null) || !ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                    return
                }
                var cf = null;
                var cg = this.$1p.get_activeSheetImpl();
                if (cg.get_isStory()) {
                    cg = cg.get_activeStoryPointImpl().get_containedSheetImpl()
                }
                if (ss.referenceEquals(cg.get_name(), e.get_worksheetName())) {
                    cf = cg
                } else if (cg.get_isDashboard()) {
                    var ch = cg;
                    cf = ch.get_worksheets()._get(e.get_worksheetName())._impl
                }
                if (ss.isValue(cf)) {
                    cf.set_selectedMarks(null);
                    this.$1$3(new bs('marksselection', this.$1m, cf))
                }
            }, $k: function (e) {
                if (ss.staticEquals(this.$1$4, null) || !ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                    return
                }
                var cf = null;
                var cg = this.$1p.get_activeSheetImpl();
                if (cg.get_isStory()) {
                    cg = cg.get_activeStoryPointImpl().get_containedSheetImpl()
                }
                if (ss.referenceEquals(cg.get_name(), e.get_worksheetName())) {
                    cf = cg
                } else if (cg.get_isDashboard()) {
                    var ch = cg;
                    cf = ch.get_worksheets()._get(e.get_worksheetName())._impl
                }
                if (ss.isValue(cf)) {
                    cf.highlightedMarks = null;
                    this.$1$4(new bp('markshighlight', this.$1m, cf))
                }
            }, $h: function (e) {
                if (ss.staticEquals(this.$1$5, null) || !ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                    return
                }
                var cf = null;
                var cg = this.$1p.get_activeSheetImpl();
                if (ss.referenceEquals(cg.get_name(), e.get_worksheetName())) {
                    cf = cg
                } else if (cg.get_isDashboard()) {
                    var ch = cg;
                    cf = ch.get_worksheets()._get(e.get_worksheetName())._impl
                } else if (cg.get_isStory()) {
                    var ci = cg;
                    var cj = ci.get_activeStoryPointImpl();
                    var ck = cj.get_containedSheetImpl();
                    if (ck.get_isDashboard()) {
                        var cl = ck;
                        cf = cl.get_worksheets()._get(e.get_worksheetName())._impl
                    } else if (ss.referenceEquals(ck.get_name(), e.get_worksheetName())) {
                        cf = ck
                    }
                }
                if (ss.isValue(cf)) {
                    var cm = JSON.parse(e.get_data());
                    var cn = cm[0];
                    var co = cm[1];
                    this.$1$5(new bn('filterchange', this.$1m, cf, cn, co))
                }
            }, $m: function (e) {
                if (!ss.staticEquals(this.$1$6, null)) {
                    if (ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                        this.$1p.$l(null);
                        var cf = e.get_data();
                        this.$D(cf)
                    }
                }
            }, $g: function (e) {
                var cf = JSON.parse(e.get_data());
                var cg = ss.mkdel(this, function () {
                    v._processCustomViews(this.$1p, this.$1g, cf)
                });
                var ch = ss.mkdel(this, function () {
                    this.$C();
                    if (!ss.staticEquals(this.$1$7, null) && !cf.customViewLoaded) {
                        this.$y(this.$1p.get_activeCustomView())
                    }
                });
                if (ss.isNullOrUndefined(this.$1p)) {
                    this.$1d = true;
                    this.$1p = new N(this, this.$1g, ss.mkdel(this, function () {
                        cg();
                        this.$w(ch);
                        this.$1d = false
                    }))
                } else {
                    cg();
                    this.$9(ch)
                }
            }, $f: function (e) {
                var cf = JSON.parse(e.get_data());
                if (ss.isNullOrUndefined(this.$1p)) {
                    this.$1p = new N(this, this.$1g, null)
                }
                if (ss.isValue(this.$1p)) {
                    v._processCustomViewUpdate(this.$1p, this.$1g, cf, true)
                }
                if (!ss.staticEquals(this.$1$8, null)) {
                    var cg = this.$1p.$p()._toApiCollection();
                    for (var ch = 0, ci = cg.length; ch < ci; ch++) {
                        this.$A(cg[ch])
                    }
                }
            }, $d: function () {
                if (!ss.staticEquals(this.$1$9, null)) {
                    var e = this.$1p.$n()._toApiCollection();
                    for (var cf = 0, cg = e.length; cf < cg; cf++) {
                        this.$z(e[cf])
                    }
                }
            }, $e: function (e) {
                var cf = JSON.parse(e.get_data());
                if (ss.isValue(this.$1p)) {
                    v._processCustomViews(this.$1p, this.$1g, cf)
                }
                if (!ss.staticEquals(this.$1$10, null) && ss.isValue(cf.defaultCustomViewId)) {
                    var cg = this.$1p.$i();
                    for (var ch = 0; ch < cg.get__length(); ch++) {
                        var ci = cg.get_item(ch);
                        if (ci.getDefault()) {
                            this.$B(ci);
                            break
                        }
                    }
                }
            }, $o: function (e) {
                this.$1p._update(ss.mkdel(this, function () {
                    if (ss.isValue(this.$18)) {
                        this.$18()
                    }
                    if (ss.referenceEquals(this.$1p.get_name(), e.get_workbookName())) {
                        var cf = e.get_worksheetName();
                        var cg = e.get_data();
                        this.$F(cf, cg)
                    }
                    this.$w(null)
                }))
            }, $n: function (e) {
                var cf = this.$1p.get_activeSheetImpl();
                if (cf.get_sheetType() === 'story') {
                    cf.update(JSON.parse(e.get_data()))
                }
            }, $w: function (e) {
                if (!this.$1h) {
                    var cf = this.$1i;
                    window.setTimeout(ss.mkdel(this, function () {
                        if (!ss.staticEquals(cf, null)) {
                            cf(new bA('firstinteractive', this.$1m))
                        }
                        if (!ss.staticEquals(e, null)) {
                            e()
                        }
                    }), 0);
                    this.$1h = true
                }
                this.$E()
            }, $9: function (e) {
                var cf = new Date;
                var cg = null;
                cg = ss.mkdel(this, function () {
                    var ch = new Date;
                    if (this.$1h) {
                        e()
                    } else if (ch - cf > 300000) {
                        throw J.createInternalError('Timed out while waiting for the viz to become interactive')
                    } else {
                        window.setTimeout(cg, 10)
                    }
                });
                cg()
            }, $2: function () {
                if (K.isIE()) {
                    if (this.$1b['readyState'] === 'complete') {
                        this.handleVizLoad()
                    }
                } else {
                    this.handleVizLoad()
                }
            }, $u: function () {
                window.setTimeout(ss.mkdel(this, this.$2), 3000)
            }, $6: function (e) {
                var cf = document.createElement('div');
                cf.style.background = "transparent url('" + this.$1k.staticImageUrl + "') no-repeat scroll 0 0";
                cf.style.left = '8px';
                cf.style.top = (this.$1k.tabs ? '31px' : '9px');
                cf.style.position = 'absolute';
                cf.style.width = e.width + 'px';
                cf.style.height = e.height + 'px';
                this.$3().appendChild(cf);
                return cf
            }, $5: function () {
                if (ss.isNullOrUndefined(this.$3())) {
                    return null
                }
                var e = document.createElement('IFrame');
                e.frameBorder = '0';
                e.setAttribute('allowTransparency', 'true');
                e.setAttribute('allowFullScreen', 'true');
                e.setAttribute('title', this.$a());
                e.marginHeight = '0';
                e.marginWidth = '0';
                e.style.display = 'block';
                if (this.$1k.fixedSize) {
                    e.style.width = this.$1k.width;
                    e.style.height = this.$1k.height
                } else {
                    e.style.width = '1px';
                    e.style.height = '1px';
                    e.setAttribute('scrolling', 'no')
                }
                if (K.isSafari()) {
                    e.addEventListener('mousewheel', ss.mkdel(this, this.$v), false)
                }
                this.$3().appendChild(e);
                return e
            }, $a: function () {
                var e = window.navigator.language;
                if (e === 'zh-CN') {
                    return '数据可视化'
                }
                switch (e.substr(0, 2)) {
                    case'fr': {
                        return 'Visualisation de données'
                    }
                    case'es': {
                        return 'Visualización de datos'
                    }
                    case'pt': {
                        return 'Visualização de dados'
                    }
                    case'ja': {
                        return 'データ ビジュアライゼーション'
                    }
                    case'de': {
                        return 'Datenvisualisierung'
                    }
                    case'ko': {
                        return '데이터 비주얼리제이션'
                    }
                    case'en':
                    default: {
                        return 'data visualization'
                    }
                }
            }, $v: function (e) {
            }, $c: function () {
                return ss.mkdel(this, function (e) {
                    this.$u()
                })
            }, $j: function (e) {
                var cf = bw.fromSizeConstraints(e.sizeConstraints);
                this.$1n = bE.$ctor(cf, e.chromeHeight);
                if (ss.isValue(this.$1j)) {
                    this.$1j(new bo('firstvizsizeknown', this.$1m, this.$1n))
                }
                if (this.$1k.fixedSize) {
                    return
                }
                this.$I();
                this.$0();
                this.$Q()
            }, $J: function () {
                if (ss.isNullOrUndefined(this.$1o)) {
                    return
                }
                if (K.hasWindowAddEventListener()) {
                    window.removeEventListener('resize', this.$1o, false)
                } else {
                    window.self.detachEvent('onresize', this.$1o)
                }
                this.$1o = null
            }, $0: function () {
                if (ss.isValue(this.$1o)) {
                    return
                }
                this.$1o = ss.mkdel(this, function () {
                    this.$I()
                });
                if (K.hasWindowAddEventListener()) {
                    window.addEventListener('resize', this.$1o, false)
                } else {
                    window.self.attachEvent('onresize', this.$1o)
                }
            }
        }, null, [bq]);
        ss.initClass(bD, a, {
            getAvailableSize: function () {
                return this.$2
            }
        }, bA);
        ss.initClass(bE, a, {}, Object);
        ss.initClass(bO, a, {
            getFilterType: function () {
                return this.$6
            }, getFieldName: function () {
                return this.$1
            }, getWorksheet: function () {
                return this.$7.get_worksheet()
            }, getFieldAsync: function () {
                var e = new tab._Deferred;
                if (ss.isNullOrUndefined(this.$3)) {
                    var cf = function (ch) {
                        e.reject(ch);
                        return null
                    };
                    var cg = ss.mkdel(this, function (ch) {
                        this.$3 = new bN(ch, this.$1, this.$5, this.$4);
                        e.resolve(this.$3);
                        return null
                    });
                    this.$7.$q(this.$2).then(cg, cf)
                } else {
                    window.setTimeout(ss.mkdel(this, function () {
                        e.resolve(this.$3)
                    }), 0)
                }
                return e.get_promise()
            }, _update: function (e) {
                this.$0(e);
                this._updateFromJson(e)
            }, _addFieldParams: function (e) {
            }, _updateFromJson: null, $0: function (e) {
                this.$1 = e.caption;
                this.$6 = S.convertFilterType(e.filterType);
                this.$3 = null;
                this.$2 = e.dataSourceName;
                this.$5 = S.convertFieldRole(ss.coalesce(e.fieldRole, 'unknown'));
                this.$4 = S.convertFieldAggregation(ss.coalesce(e.fieldAggregation, 'NONE'))
            }
        });
        ss.initClass(bG, a, {
            getIsExcludeMode: function () {
                return this.$a
            }, getAppliedValues: function () {
                return this.$9
            }, _updateFromJson: function (e) {
                this.$8(e)
            }, $8: function (e) {
                this.$a = e.isExclude;
                if (ss.isValue(e.appliedValues)) {
                    this.$9 = [];
                    for (var cf = 0; cf < e.appliedValues.length; cf++) {
                        var cg = e.appliedValues[cf];
                        this.$9.push(K.getDataValue(cg))
                    }
                }
            }
        }, bO);
        ss.initClass(bH, a, {
            getFieldName: function () {
                return this.$0.get_fieldName()
            }, getDataType: function () {
                return this.$0.get_dataType()
            }, getIsReferenced: function () {
                return this.$0.get_isReferenced()
            }, getIndex: function () {
                return this.$0.get_index()
            }
        });
        ss.initClass(bI, a, {
            getWorkbook: function () {
                return this._impl.$b()
            }, getUrl: function () {
                return this._impl.$a()
            }, getName: function () {
                return this._impl.$7()
            }, setName: function (e) {
                this._impl.$8(e)
            }, getOwnerName: function () {
                return this._impl.$9()
            }, getAdvertised: function () {
                return this._impl.$3()
            }, setAdvertised: function (e) {
                this._impl.$4(e)
            }, getDefault: function () {
                return this._impl.$6()
            }, saveAsync: function () {
                return this._impl.$2()
            }
        });
        ss.initClass(bV, a, {
            getName: function () {
                return this._impl.get_name()
            }, getIndex: function () {
                return this._impl.get_index()
            }, getWorkbook: function () {
                return this._impl.get_workbookImpl().get_workbook()
            }, getSize: function () {
                return this._impl.get_size()
            }, getIsHidden: function () {
                return this._impl.get_isHidden()
            }, getIsActive: function () {
                return this._impl.get_isActive()
            }, getSheetType: function () {
                return this._impl.get_sheetType()
            }, getUrl: function () {
                return this._impl.get_url()
            }, changeSizeAsync: function (e) {
                return this._impl.changeSizeAsync(e)
            }
        });
        ss.initClass(bJ, a, {
            getParentStoryPoint: function () {
                return this._impl.get_parentStoryPoint()
            }, getObjects: function () {
                return this._impl.get_objects()._toApiCollection()
            }, getWorksheets: function () {
                return this._impl.get_worksheets()._toApiCollection()
            }
        }, bV);
        ss.initClass(bK, a, {
            getObjectType: function () {
                return this.$2.objectType
            }, getDashboard: function () {
                return this.$0
            }, getWorksheet: function () {
                return this.$1
            }, getPosition: function () {
                return this.$2.position
            }, getSize: function () {
                return this.$2.size
            }
        });
        ss.initClass(bL, a, {
            getName: function () {
                return this.$0.get_name()
            }, getFields: function () {
                return this.$0.get_fields()._toApiCollection()
            }, getIsPrimary: function () {
                return this.$0.get_isPrimary()
            }
        });
        ss.initClass(bM, a, {
            getName: function () {
                return this.$0.get_name()
            }, getData: function () {
                return this.$0.get_rows()
            }, getColumns: function () {
                return this.$0.get_columns()
            }, getTotalRowCount: function () {
                return this.$0.get_totalRowCount()
            }, getIsSummaryData: function () {
                return this.$0.get_isSummaryData()
            }
        });
        ss.initClass(bN, a, {
            getDataSource: function () {
                return this.$0
            }, getName: function () {
                return this.$3
            }, getRole: function () {
                return this.$2
            }, getAggregation: function () {
                return this.$1
            }
        });
        ss.initClass(bP, a, {
            _addFieldParams: function (e) {
                e['api.filterHierarchicalLevels'] = this.$9
            }, _updateFromJson: function (e) {
                this.$8(e)
            }, $8: function (e) {
                this.$9 = e.levels
            }
        }, bO);
        ss.initClass(bQ, a, {
            getPairs: function () {
                return this.$0.$1()
            }
        });
        ss.initClass(bR, a, {});
        ss.initClass(bS, a, {
            getName: function () {
                return this._impl.$7()
            }, getCurrentValue: function () {
                return this._impl.$2()
            }, getDataType: function () {
                return this._impl.$3()
            }, getAllowableValuesType: function () {
                return this._impl.$1()
            }, getAllowableValues: function () {
                return this._impl.$0()
            }, getMinValue: function () {
                return this._impl.$6()
            }, getMaxValue: function () {
                return this._impl.$5()
            }, getStepSize: function () {
                return this._impl.$9()
            }, getDateStepPeriod: function () {
                return this._impl.$4()
            }
        });
        ss.initClass(bT, a, {
            getMin: function () {
                return this.$d
            }, getMax: function () {
                return this.$c
            }, getIncludeNullValues: function () {
                return this.$b
            }, getDomainMin: function () {
                return this.$a
            }, getDomainMax: function () {
                return this.$9
            }, _updateFromJson: function (e) {
                this.$8(e)
            }, $8: function (e) {
                this.$a = K.getDataValue(e.domainMinValue);
                this.$9 = K.getDataValue(e.domainMaxValue);
                this.$d = K.getDataValue(e.minValue);
                this.$c = K.getDataValue(e.maxValue);
                this.$b = e.includeNullValues
            }
        }, bO);
        ss.initClass(bU, a, {
            getPeriod: function () {
                return this.$9
            }, getRange: function () {
                return this.$b
            }, getRangeN: function () {
                return this.$a
            }, _updateFromJson: function (e) {
                this.$8(e)
            }, $8: function (e) {
                if (ss.isValue(e.periodType)) {
                    this.$9 = S.convertPeriodType(ss.unbox(e.periodType))
                }
                if (ss.isValue(e.rangeType)) {
                    this.$b = S.convertDateRange(ss.unbox(e.rangeType))
                }
                if (ss.isValue(e.rangeN)) {
                    this.$a = ss.unbox(e.rangeN)
                }
            }
        }, bO);
        ss.initClass(bW, a, {
            getName: function () {
                return this.$0.name
            }, getSheetType: function () {
                return this.$0.sheetType
            }, getSize: function () {
                return this.$0.size
            }, getIndex: function () {
                return this.$0.index
            }, getUrl: function () {
                return this.$0.url
            }, getIsActive: function () {
                return this.$0.isActive
            }, getIsHidden: function () {
                return this.$0.isHidden
            }, getWorkbook: function () {
                return this.$0.workbook
            }
        });
        ss.initClass(bX, a, {
            getActiveStoryPoint: function () {
                return this._impl.get_activeStoryPointImpl().get_storyPoint()
            }, getStoryPointsInfo: function () {
                return this._impl.get_storyPointsInfo()
            }, activatePreviousStoryPointAsync: function () {
                return this._impl.activatePreviousStoryPointAsync()
            }, activateNextStoryPointAsync: function () {
                return this._impl.activateNextStoryPointAsync()
            }, activateStoryPointAsync: function (e) {
                return this._impl.activateStoryPointAsync(e)
            }, revertStoryPointAsync: function (e) {
                return this._impl.revertStoryPointAsync(e)
            }
        }, bV);
        ss.initClass(bY, a, {
            getCaption: function () {
                return this.$0.get_caption()
            }, getContainedSheet: function () {
                return (ss.isValue(this.$0.get_containedSheetImpl()) ? this.$0.get_containedSheetImpl().get_sheet() : null)
            }, getIndex: function () {
                return this.$0.get_index()
            }, getIsActive: function () {
                return this.$0.get_isActive()
            }, getIsUpdated: function () {
                return this.$0.get_isUpdated()
            }, getParentStory: function () {
                return this.$0.get_parentStoryImpl().get_story()
            }
        });
        ss.initClass(bZ, a, {
            getCaption: function () {
                return this._impl.caption
            }, getIndex: function () {
                return this._impl.index
            }, getIsActive: function () {
                return this._impl.isActive
            }, getIsUpdated: function () {
                return this._impl.isUpdated
            }, getParentStory: function () {
                return this._impl.parentStoryImpl.get_story()
            }
        });
        ss.initClass(ca, a, {
            getMajor: function () {
                return this.$0
            }, getMinor: function () {
                return this.$2
            }, getPatch: function () {
                return this.$3
            }, getMetadata: function () {
                return this.$1
            }, toString: function () {
                var e = this.$0 + '.' + this.$2 + '.' + this.$3;
                if (ss.isValue(this.$1) && this.$1.length > 0) {
                    e += '-' + this.$1
                }
                return e
            }
        });
        ss.initClass(cb, a, {
            getAreTabsHidden: function () {
                return this._impl.$10()
            }, getIsToolbarHidden: function () {
                return this._impl.$12()
            }, getIsHidden: function () {
                return this._impl.$11()
            }, getInstanceId: function () {
                return this._impl.get_instanceId()
            }, getParentElement: function () {
                return this._impl.$13()
            }, getUrl: function () {
                return this._impl.$14()
            }, getVizSize: function () {
                return this._impl.$16()
            }, getWorkbook: function () {
                return this._impl.$17()
            }, getAreAutomaticUpdatesPaused: function () {
                return this._impl.$Z()
            }, getCurrentUrlAsync: function () {
                return this._impl.getCurrentUrlAsync()
            }, addEventListener: function (e, cf) {
                this._impl.addEventListener(e, cf)
            }, removeEventListener: function (e, cf) {
                this._impl.removeEventListener(e, cf)
            }, dispose: function () {
                this._impl.$7()
            }, show: function () {
                this._impl.$Q()
            }, hide: function () {
                this._impl.$q()
            }, showExportDataDialog: function (e) {
                this._impl.$T(e)
            }, showExportCrossTabDialog: function (e) {
                this._impl.$S(e)
            }, showExportImageDialog: function () {
                this._impl.$U()
            }, showExportPDFDialog: function () {
                this._impl.$V()
            }, revertAllAsync: function () {
                return this._impl.$L()
            }, refreshDataAsync: function () {
                return this._impl.$H()
            }, showShareDialog: function () {
                this._impl.$W()
            }, showDownloadWorkbookDialog: function () {
                this._impl.$R()
            }, pauseAutomaticUpdatesAsync: function () {
                return this._impl.$x()
            }, resumeAutomaticUpdatesAsync: function () {
                return this._impl.$K()
            }, toggleAutomaticUpdatesAsync: function () {
                return this._impl.$X()
            }, refreshSize: function () {
                this._impl.$I()
            }, setFrameSize: function (e, cf) {
                var cg = e;
                var ch = cf;
                if (K.isNumber(e)) {
                    cg = e.toString() + 'px'
                }
                if (K.isNumber(cf)) {
                    ch = cf.toString() + 'px'
                }
                this._impl.$P(cg, ch)
            }
        });
        ss.initClass(cc, a, {});
        ss.initClass(cd, a, {
            getViz: function () {
                return this.$0.get_viz()
            }, getPublishedSheetsInfo: function () {
                return this.$0.get_publishedSheets()._toApiCollection()
            }, getName: function () {
                return this.$0.get_name()
            }, getActiveSheet: function () {
                return this.$0.get_activeSheetImpl().get_sheet()
            }, getActiveCustomView: function () {
                return this.$0.get_activeCustomView()
            }, activateSheetAsync: function (e) {
                return this.$0._setActiveSheetAsync(e)
            }, revertAllAsync: function () {
                return this.$0._revertAllAsync()
            }, getCustomViewsAsync: function () {
                return this.$0.$6()
            }, showCustomViewAsync: function (e) {
                return this.$0.$f(e)
            }, removeCustomViewAsync: function (e) {
                return this.$0.$c(e)
            }, rememberCustomViewAsync: function (e) {
                return this.$0.$b(e)
            }, setActiveCustomViewAsDefaultAsync: function () {
                return this.$0.$e()
            }, getParametersAsync: function () {
                return this.$0.$7()
            }, changeParameterValueAsync: function (e, cf) {
                return this.$0.$2(e, cf)
            }
        });
        ss.initClass(ce, a, {
            getParentDashboard: function () {
                return this._impl.get_parentDashboard()
            }, getParentStoryPoint: function () {
                return this._impl.get_parentStoryPoint()
            }, getDataSourcesAsync: function () {
                return this._impl.$r()
            }, getFilterAsync: function (e, cf) {
                return this._impl.$s(null, e, cf)
            }, getFiltersAsync: function (e) {
                return this._impl.$t(e)
            }, applyFilterAsync: function (e, cf, cg, ch) {
                return this._impl.$e(e, cf, cg, ch)
            }, clearFilterAsync: function (e) {
                return this._impl.$m(e)
            }, applyRangeFilterAsync: function (e, cf) {
                return this._impl.$i(e, cf)
            }, applyRelativeDateFilterAsync: function (e, cf) {
                return this._impl.$k(e, cf)
            }, applyHierarchicalFilterAsync: function (e, cf, cg, ch) {
                return this._impl.$g(e, cf, cg, ch)
            }, clearSelectedMarksAsync: function () {
                return this._impl.$p()
            }, selectMarksAsync: function (e, cf, cg) {
                return this._impl.$B(e, cf, cg)
            }, getSelectedMarksAsync: function () {
                return this._impl.$v()
            }, getSummaryDataAsync: function (e) {
                return this._impl.$w(e)
            }, getUnderlyingDataAsync: function (e) {
                return this._impl.$x(e)
            }, clearHighlightedMarksAsync: function () {
                return this._impl.$o()
            }, highlightMarksAsync: function (e, cf) {
                return this._impl.$y(e, cf)
            }, highlightMarksByPatternMatchAsync: function (e, cf) {
                return this._impl.$z(e, cf)
            }, getHighlightedMarksAsync: function () {
                return this._impl.$u()
            }
        }, bV);
        (function () {
            p.crossDomainEventNotificationId = 'xdomainSourceId';
            p.$0 = 0
        })();
        (function () {
            L.$5 = []
        })();
        (function () {
            A.$0 = 'array';
            A.$1 = 'boolean';
            A.$2 = 'date';
            A.$3 = 'function';
            A.$4 = 'number';
            A.$5 = 'object';
            A.$6 = 'regexp';
            A.$7 = 'string';
            A.$8 = ss.mkdict(['[object Boolean]', 'boolean', '[object Number]', 'number', '[object String]', 'string', '[object Function]', 'function', '[object Array]', 'array', '[object Date]', 'date', '[object RegExp]', 'regexp', '[object Object]', 'object']);
            A.$e = String.prototype['trim'];
            A.$d = Object.prototype['toString'];
            A.$f = new RegExp('^[\\s\\xA0]+');
            A.$g = new RegExp('[\\s\\xA0]+$');
            A.$a = new RegExp('^[\\],:{}\\s]*$');
            A.$b = new RegExp('\\\\(?:["\\\\\\/bfnrt]|u[0-9a-fA-F]{4})', 'g');
            A.$c = new RegExp('"[^"\\\\\\n\\r]*"|true|false|null|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?', 'g');
            A.$9 = new RegExp('(?:^|:|,)(?:\\s*\\[)+', 'g')
        })();
        (function () {
            var e = global.tableauSoftware;
            e.DeviceType = {DEFAULT: 'default', DESKTOP: 'desktop', TABLET: 'tablet', PHONE: 'phone'};
            e.DashboardObjectType = {
                BLANK: 'blank',
                WORKSHEET: 'worksheet',
                QUICK_FILTER: 'quickFilter',
                PARAMETER_CONTROL: 'parameterControl',
                PAGE_FILTER: 'pageFilter',
                LEGEND: 'legend',
                TITLE: 'title',
                TEXT: 'text',
                IMAGE: 'image',
                WEB_PAGE: 'webPage'
            };
            e.DataType = {FLOAT: 'float', INTEGER: 'integer', STRING: 'string', BOOLEAN: 'boolean', DATE: 'date', DATETIME: 'datetime'};
            e.DateRangeType = {LAST: 'last', LASTN: 'lastn', NEXT: 'next', NEXTN: 'nextn', CURR: 'curr', TODATE: 'todate'};
            e.ErrorCode = {
                INTERNAL_ERROR: 'internalError',
                SERVER_ERROR: 'serverError',
                INVALID_AGGREGATION_FIELD_NAME: 'invalidAggregationFieldName',
                INVALID_PARAMETER: 'invalidParameter',
                INVALID_URL: 'invalidUrl',
                STALE_DATA_REFERENCE: 'staleDataReference',
                VIZ_ALREADY_IN_MANAGER: 'vizAlreadyInManager',
                NO_URL_OR_PARENT_ELEMENT_NOT_FOUND: 'noUrlOrParentElementNotFound',
                INVALID_FILTER_FIELDNAME: 'invalidFilterFieldName',
                INVALID_FILTER_FIELDVALUE: 'invalidFilterFieldValue',
                INVALID_FILTER_FIELDNAME_OR_VALUE: 'invalidFilterFieldNameOrValue',
                FILTER_CANNOT_BE_PERFORMED: 'filterCannotBePerformed',
                NOT_ACTIVE_SHEET: 'notActiveSheet',
                INVALID_CUSTOM_VIEW_NAME: 'invalidCustomViewName',
                MISSING_RANGEN_FOR_RELATIVE_DATE_FILTERS: 'missingRangeNForRelativeDateFilters',
                MISSING_MAX_SIZE: 'missingMaxSize',
                MISSING_MIN_SIZE: 'missingMinSize',
                MISSING_MINMAX_SIZE: 'missingMinMaxSize',
                INVALID_SIZE: 'invalidSize',
                INVALID_SIZE_BEHAVIOR_ON_WORKSHEET: 'invalidSizeBehaviorOnWorksheet',
                SHEET_NOT_IN_WORKBOOK: 'sheetNotInWorkbook',
                INDEX_OUT_OF_RANGE: 'indexOutOfRange',
                DOWNLOAD_WORKBOOK_NOT_ALLOWED: 'downloadWorkbookNotAllowed',
                NULL_OR_EMPTY_PARAMETER: 'nullOrEmptyParameter',
                BROWSER_NOT_CAPABLE: 'browserNotCapable',
                UNSUPPORTED_EVENT_NAME: 'unsupportedEventName',
                INVALID_DATE_PARAMETER: 'invalidDateParameter',
                INVALID_SELECTION_FIELDNAME: 'invalidSelectionFieldName',
                INVALID_SELECTION_VALUE: 'invalidSelectionValue',
                INVALID_SELECTION_DATE: 'invalidSelectionDate',
                NO_URL_FOR_HIDDEN_WORKSHEET: 'noUrlForHiddenWorksheet',
                MAX_VIZ_RESIZE_ATTEMPTS: 'maxVizResizeAttempts'
            };
            e.FieldAggregationType = {
                SUM: 'SUM',
                AVG: 'AVG',
                MIN: 'MIN',
                MAX: 'MAX',
                STDEV: 'STDEV',
                STDEVP: 'STDEVP',
                VAR: 'VAR',
                VARP: 'VARP',
                COUNT: 'COUNT',
                COUNTD: 'COUNTD',
                MEDIAN: 'MEDIAN',
                ATTR: 'ATTR',
                NONE: 'NONE',
                PERCENTILE: 'PERCENTILE',
                YEAR: 'YEAR',
                QTR: 'QTR',
                MONTH: 'MONTH',
                DAY: 'DAY',
                HOUR: 'HOUR',
                MINUTE: 'MINUTE',
                SECOND: 'SECOND',
                WEEK: 'WEEK',
                WEEKDAY: 'WEEKDAY',
                MONTHYEAR: 'MONTHYEAR',
                MDY: 'MDY',
                END: 'END',
                TRUNC_YEAR: 'TRUNC_YEAR',
                TRUNC_QTR: 'TRUNC_QTR',
                TRUNC_MONTH: 'TRUNC_MONTH',
                TRUNC_WEEK: 'TRUNC_WEEK',
                TRUNC_DAY: 'TRUNC_DAY',
                TRUNC_HOUR: 'TRUNC_HOUR',
                TRUNC_MINUTE: 'TRUNC_MINUTE',
                TRUNC_SECOND: 'TRUNC_SECOND',
                QUART1: 'QUART1',
                QUART3: 'QUART3',
                SKEWNESS: 'SKEWNESS',
                KURTOSIS: 'KURTOSIS',
                INOUT: 'INOUT',
                SUM_XSQR: 'SUM_XSQR',
                USER: 'USER'
            };
            e.FieldRoleType = {DIMENSION: 'dimension', MEASURE: 'measure', UNKNOWN: 'unknown'};
            e.FilterUpdateType = {ALL: 'all', REPLACE: 'replace', ADD: 'add', REMOVE: 'remove'};
            e.FilterType = {CATEGORICAL: 'categorical', QUANTITATIVE: 'quantitative', HIERARCHICAL: 'hierarchical', RELATIVEDATE: 'relativedate'};
            e.NullOption = {NULL_VALUES: 'nullValues', NON_NULL_VALUES: 'nonNullValues', ALL_VALUES: 'allValues'};
            e.ParameterAllowableValuesType = {ALL: 'all', LIST: 'list', RANGE: 'range'};
            e.ParameterDataType = {FLOAT: 'float', INTEGER: 'integer', STRING: 'string', BOOLEAN: 'boolean', DATE: 'date', DATETIME: 'datetime'};
            e.PeriodType = {YEAR: 'year', QUARTER: 'quarter', MONTH: 'month', WEEK: 'week', DAY: 'day', HOUR: 'hour', MINUTE: 'minute', SECOND: 'second'};
            e.SelectionUpdateType = {REPLACE: 'replace', ADD: 'add', REMOVE: 'remove'};
            e.SheetSizeBehavior = {AUTOMATIC: 'automatic', EXACTLY: 'exactly', RANGE: 'range', ATLEAST: 'atleast', ATMOST: 'atmost'};
            e.SheetType = {WORKSHEET: 'worksheet', DASHBOARD: 'dashboard', STORY: 'story'};
            e.TableauEventName = {
                CUSTOM_VIEW_LOAD: 'customviewload',
                CUSTOM_VIEW_REMOVE: 'customviewremove',
                CUSTOM_VIEW_SAVE: 'customviewsave',
                CUSTOM_VIEW_SET_DEFAULT: 'customviewsetdefault',
                FILTER_CHANGE: 'filterchange',
                FIRST_INTERACTIVE: 'firstinteractive',
                FIRST_VIZ_SIZE_KNOWN: 'firstvizsizeknown',
                MARKS_SELECTION: 'marksselection',
                MARKS_HIGHLIGHT: 'markshighlight',
                PARAMETER_VALUE_CHANGE: 'parametervaluechange',
                STORY_POINT_SWITCH: 'storypointswitch',
                TAB_SWITCH: 'tabswitch',
                VIZ_RESIZE: 'vizresize'
            };
            e.ToolbarPosition = {TOP: 'top', BOTTOM: 'bottom'}
        })();
        (function () {
            q.$4 = null;
            q.$5 = null
        })();
        (function () {
            E.noZoneId = 4294967295
        })();
        (function () {
            O.$5 = new RegExp('\\[[^\\]]+\\]\\.', 'g')
        })();
        (function () {
            ca.$0 = new ca(2, 1, 2, 'null')
        })()
    })();
    window.tableau = window.tableauSoftware = global.tableauSoftware;
    tableauSoftware.Promise = tab._PromiseImpl;
    tab._Deferred = tab._DeferredImpl;
    tab._Collection = tab._CollectionImpl;
    tab._ApiBootstrap.initialize()
})();