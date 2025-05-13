<# Example usage in Windows Powershell:
.\ReplaceHexBytesAll.ps1 -filePath "D:\TEMP\file.exe" -patterns "4883EC28BA2F????00??8D0DB0B7380A/11111111111111111111111111111111","C4 25 2A 0A 48 89 45 18 48 8D 55 18 48 8D 4D ?? /     1111 111111    111111 1111111111111111","\x45\xA8\x48\x8D\x55\xA8\x48\x8D\x4D\x68\xE8\x61\x8C\x1E\x05\xBA/\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11","??1FBA0E??????CD21B8014CCD21????/????????????????74C3????????????" -makeBackup -showMoreInfo -skipStopwatch #>

# Main script
param (
    [Parameter(Mandatory)]
    [string]$filePath,
    [switch]$makeBackup = $false,
    [switch]$showMoreInfo = $false,
    [switch]$skipStopwatch = $false,
    # One pattern is string with search/replace hex
    # like "AABB/1122" or "\xAA\xBB/\x11\x22" or "A A BB CC|1 12 233" or "?? AA BB CC??FF/112233445566" or "AABB??CC????11/??C3??????????"
    [Parameter(Mandatory)]
    [string[]]$patterns
)

if (-not (Test-Path $filePath)) {
    Write-Error "File not found: $filePath"
    exit 1
}

if ($patterns.Count -eq 0) {
    Write-Error "No patterns given"
    exit 1
}


# =====
# GLOBAL VARIABLES
# =====

$PSHost = If ($PSVersionTable.PSVersion.Major -le 5) { 'PowerShell' } Else { 'PwSh' }
[string]$PSBoundParametersStringGlobal = ($PSBoundParameters.GetEnumerator() | ForEach-Object {
        if ($_.Value -is [array]) {
            # If value is array - it array with patterns and we need concat it to 1 string
            $tempValue = $_.Value -join ','
            return "-$($_.Key) `"$tempValue`""
        }

        if (Test-Path $_.Value) {
            $tempValue = [System.IO.Path]::GetFullPath($_.Value)
            return "-$($_.Key) `"$tempValue`""
        }

        return "-$($_.Key) `"$($_.Value)`""
    }) -join " "

[string]$filePathFull = [System.IO.Path]::GetFullPath($filePath)

# C# code from HexHandler.cs minified using https://atifaziz.github.io/CSharpMinifierDemo/
[string]$hexHandlerCodeMinified = @"
using System;using System.IO;using System.Globalization;using System.Collections.Generic;using System.Linq;namespace HexHandler{public sealed class BytesHandler:IDisposable{private readonly Stream stream;private readonly int bufferSize;private const string wildcard="??";private const string wildcardInRegExp="[\\x00-\\xFF]";public BytesHandler(Stream stream,int bufferSize=ushort.MaxValue){if(bufferSize<2)throw new ArgumentOutOfRangeException("bufferSize less than 2 bytes");this.stream=stream;this.bufferSize=bufferSize;}private static byte[]ConvertHexStringToByteArray(string hexString){string hexStringCleaned=hexString.Replace(" ",string.Empty).Replace("\\x",string.Empty).Replace("0x",string.Empty).Replace(",",string.Empty).Normalize().Trim();if(hexStringCleaned.Length%2!=0){throw new ArgumentException(string.Format(CultureInfo.InvariantCulture,"The binary key cannot have an odd number of digits: {0}",hexStringCleaned));}byte[]data=new byte[hexStringCleaned.Length/2];try{for(int index=0;index<data.Length;index++){string byteValue=hexStringCleaned.Substring(index*2,2);data[index]=byte.Parse(byteValue,NumberStyles.HexNumber,CultureInfo.InvariantCulture);}}catch(FormatException){throw new FormatException("Hex string "+hexString+" or it cleaned version "+hexStringCleaned+" contain not HEX symbols and cannot be converted to bytes array");}return data;}private static Tuple<byte[],bool[]>ConvertHexStringWithWildcardsToByteArrayAndMask(string hexString,string wildcardExample=wildcard){string hexStringCleaned=hexString.Replace(" ",string.Empty).Replace(wildcardInRegExp,wildcardExample).Replace("\\x",string.Empty).Replace("0x",string.Empty).Replace(",",string.Empty).Normalize().Trim();if(hexStringCleaned.Length%2!=0){throw new ArgumentException(string.Format(CultureInfo.InvariantCulture,"The binary key cannot have an odd number of digits: {0}",hexStringCleaned));}byte[]data=new byte[hexStringCleaned.Length/2];bool[]mask=new bool[data.Length];try{for(int index=0;index<data.Length;index++){string byteValue=hexStringCleaned.Substring(index*2,2);if(byteValue==wildcardExample){data[index]=byte.Parse("00",NumberStyles.HexNumber,CultureInfo.InvariantCulture);mask[index]=true;}else{data[index]=byte.Parse(byteValue,NumberStyles.HexNumber,CultureInfo.InvariantCulture);mask[index]=false;}}}catch(FormatException){throw new FormatException("Hex string "+hexString+" or it cleaned version "+hexStringCleaned+" contain not HEX symbols and cannot be converted to bytes array");}return Tuple.Create(data,mask);}private bool TestHexStringContainWildcards(string hexString,string wildcardExample=wildcard){string hexStringCleaned=hexString.Replace(" ",string.Empty).Replace(wildcardInRegExp,wildcardExample);return hexStringCleaned.IndexOf(wildcardExample)!=-1||hexStringCleaned.IndexOf(wildcardInRegExp)!=-1;}private byte[]CreateArrayFilledIdenticalBytes(int size,byte element){byte[]result=new byte[size];for(int i=0;i<size;i++){result[i]=element;}return result;}private bool DoesStreamHaveSequenceInPosition(byte[]sequence,long position){if(sequence.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",sequence.Length,bufferSize));if(position<0)throw new ArgumentOutOfRangeException("position should more than zero");if(position>stream.Length)throw new ArgumentOutOfRangeException("position must be within the stream body");byte[]buffer=new byte[sequence.Length];stream.Position=position;stream.Read(buffer,0,buffer.Length);for(int i=0;i<sequence.Length;i++){if(buffer[i]!=sequence[i]){return false;}}return true;}private bool DoesStreamHaveSequenceInPosition_WithWildcardsMask(byte[]sequence,bool[]wildcardsMask,long position){if(sequence.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",sequence.Length,bufferSize));if(position<0)throw new ArgumentOutOfRangeException("position should more than zero");if(position>stream.Length)throw new ArgumentOutOfRangeException("position must be within the stream body");byte[]buffer=new byte[sequence.Length];stream.Position=position;stream.Read(buffer,0,buffer.Length);for(int i=0;i<sequence.Length;i++){if(!wildcardsMask[i]&&buffer[i]!=sequence[i]){return false;}}return true;}private Tuple<byte[],Tuple<int,int>>extractArrayWithoutDuplicatesAtEdges(byte[]searchPattern){int skipFromStart=0;int skipFromEnd=0;if(searchPattern.Distinct().Count()==1){return Tuple.Create(new byte[]{searchPattern[0]},Tuple.Create(0,searchPattern.Length-2));}for(int i=1;i<searchPattern.Length;i++){if(searchPattern[i]!=searchPattern[i-1]){break;}skipFromStart++;}for(int i=searchPattern.Length-2;i>0;i--){if(searchPattern[i]!=searchPattern[i+1]){break;}skipFromEnd++;}int newLength=searchPattern.Length-skipFromStart-skipFromEnd;byte[]result=new byte[newLength];Array.Copy(searchPattern,skipFromStart,result,0,newLength);return Tuple.Create(result,Tuple.Create(skipFromStart,skipFromEnd));}private Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(byte[]searchPattern,bool[]wildcardsMask){int skipFromStart=0;int skipFromEnd=0;for(int i=0;i<wildcardsMask.Length;i++){if(!wildcardsMask[i]){break;}skipFromStart++;}for(int i=wildcardsMask.Length-1;i>0;i--){if(!wildcardsMask[i]){break;}skipFromEnd++;}int newLength=wildcardsMask.Length-skipFromStart-skipFromEnd;byte[]resultBytes=new byte[newLength];bool[]resultWildCards=new bool[newLength];Array.Copy(searchPattern,skipFromStart,resultBytes,0,newLength);Array.Copy(wildcardsMask,skipFromStart,resultWildCards,0,newLength);return Tuple.Create(Tuple.Create(resultBytes,resultWildCards),Tuple.Create(skipFromStart,skipFromEnd));}public bool StartsWith(byte[]searchPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));return DoesStreamHaveSequenceInPosition(searchPattern,0);}public bool StartsWith(string searchPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;return DoesStreamHaveSequenceInPosition_WithWildcardsMask(searchPatternBytes,wildcardsMask,0);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);return StartsWith(searchPatternBytes);}}public bool EndsWith(byte[]searchPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));return DoesStreamHaveSequenceInPosition(searchPattern,stream.Length-searchPattern.Length);}public bool EndsWith(string searchPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;return DoesStreamHaveSequenceInPosition_WithWildcardsMask(searchPatternBytes,wildcardsMask,stream.Length-searchPatternBytes.Length);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);return EndsWith(searchPatternBytes);}}public long[]OverwriteBytesAtPatternPositions(byte[]searchPattern,byte[]insertPattern,int amount){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(insertPattern==null)throw new ArgumentNullException("insertPattern argument not given");if(amount>stream.Length)throw new ArgumentOutOfRangeException("amount overwrite occurrences should be less than count bytes in stream");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));long[]foundPositions=Find(searchPattern,amount);if(foundPositions.Length>1&&foundPositions[0]!=-1){for(int i=0;i<foundPositions.Length;i++){stream.Seek(foundPositions[i],SeekOrigin.Begin);stream.Write(insertPattern,0,insertPattern.Length);}}return foundPositions;}public long[]OverwriteBytesAtPatternPositions(string searchPattern,string insertPattern,int amount){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");if(string.IsNullOrEmpty(insertPattern))throw new ArgumentNullException("insertPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);long[]offsets;if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;offsets=Find_WithWildcardsMask(searchPatternBytes,wildcardsMask,amount);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);offsets=Find(searchPatternBytes,amount);}if(offsets.Length>0&&offsets[0]!=-1){for(int i=0;i<offsets.Length;i++){PasteBytesSequenceAtOffset(insertPattern,offsets[i]);}}return offsets;}public long[]OverwriteBytesAtAllPatternPositions(byte[]searchPattern,byte[]insertPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(insertPattern==null)throw new ArgumentNullException("insertPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));long[]foundPositions=FindAll(searchPattern);if(foundPositions.Length>1&&foundPositions[0]!=-1){for(int i=0;i<foundPositions.Length;i++){stream.Seek(foundPositions[i],SeekOrigin.Begin);stream.Write(insertPattern,0,insertPattern.Length);}}return foundPositions;}public long[]OverwriteBytesAtAllPatternPositions(string searchPattern,string insertPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");if(string.IsNullOrEmpty(insertPattern))throw new ArgumentNullException("insertPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);long[]offsets;if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;offsets=FindAll_WithWildcardsMask(searchPatternBytes,wildcardsMask);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);offsets=FindAll(searchPatternBytes);}if(offsets.Length>0&&offsets[0]!=-1){for(int i=0;i<offsets.Length;i++){PasteBytesSequenceAtOffset(insertPattern,offsets[i]);}}return offsets;}public long OverwriteBytesAtFirstPatternPosition(byte[]searchPattern,byte[]insertPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(insertPattern==null)throw new ArgumentNullException("insertPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));long foundPosition=FindFirst(searchPattern);if(foundPosition!=-1){stream.Seek(foundPosition,SeekOrigin.Begin);stream.Write(insertPattern,0,insertPattern.Length);}return foundPosition;}public long OverwriteBytesAtFirstPatternPosition(string searchPattern,string insertPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");if(string.IsNullOrEmpty(insertPattern))throw new ArgumentNullException("insertPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);long offset;if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(searchPatternBytes,wildcardsMask);byte[]genuineArray=extractedData.Item1.Item1;bool[]genuineMask=extractedData.Item1.Item2;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;offset=FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,0,skippedFromStart,skippedFromEnd);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);offset=FindFirst(searchPatternBytes);}if(offset!=-1){PasteBytesSequenceAtOffset(insertPattern,offset);}return offset;}public long FindFromPosition(byte[]searchPattern,long position=0,int skippedFromStart=0,int skippedFromEnd=0,long stepBackFromEnd=0){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(position<0)throw new ArgumentOutOfRangeException("position should more than zero");if(position>stream.Length)throw new ArgumentOutOfRangeException("position must be within the stream body");if(searchPattern.Length+skippedFromStart+skippedFromEnd>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));long foundPosition=-1;byte[]buffer=new byte[bufferSize+searchPattern.Length-1];int bytesRead;stream.Position=position;bool isPatternHaveDuplicatesAtEdges=skippedFromStart>0||skippedFromEnd>0;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){int index=0;while(index<=(bytesRead-searchPattern.Length)){int foundIndex=Array.IndexOf(buffer,searchPattern[0],index);if(foundIndex==-1||foundIndex+searchPattern.Length>buffer.Length)break;bool match=true;for(int j=1;j<searchPattern.Length;j++){if(buffer[foundIndex+j]!=searchPattern[j]){match=false;break;}}if(match){foundPosition=position+foundIndex;if(isPatternHaveDuplicatesAtEdges){if(skippedFromStart>foundPosition||foundPosition-skippedFromStart<position){match=false;index=foundIndex+1;continue;}if(skippedFromEnd>stream.Length-foundPosition-stepBackFromEnd){return-1;}if(skippedFromStart>0){byte[]skippedBytes=CreateArrayFilledIdenticalBytes(skippedFromStart,searchPattern[0]);if(!DoesStreamHaveSequenceInPosition(skippedBytes,foundPosition-skippedFromStart)){match=false;index=foundIndex+1;continue;}}if(skippedFromEnd>0){byte[]skippedBytes=CreateArrayFilledIdenticalBytes(skippedFromEnd,searchPattern[searchPattern.Length-1]);if(!DoesStreamHaveSequenceInPosition(skippedBytes,foundPosition+searchPattern.Length+1)){match=false;index=foundIndex+searchPattern.Length+1;continue;}}return foundPosition-skippedFromStart;}else{return foundPosition;}}else{index=foundIndex+1;}}position+=bytesRead-searchPattern.Length+1;if(position>stream.Length-searchPattern.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return-1;}private long FindFromPosition_WithWildcardsMask(byte[]searchPattern,bool[]wildcardsMask,long position=0,int skippedFromStart=0,int skippedFromEnd=0){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(wildcardsMask==null)throw new ArgumentNullException("wildcardsMask argument not given");if(searchPattern.Length!=wildcardsMask.Length)throw new ArgumentException("wildcardsMask and search pattern must be same length");if(position<0)throw new ArgumentOutOfRangeException("position should more than zero");if(position>stream.Length)throw new ArgumentOutOfRangeException("position must be within the stream body");if(searchPattern.Length+skippedFromStart+skippedFromEnd>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));bool isMaskFilledWildcards=Array.TrueForAll(wildcardsMask,x=>x);if(isMaskFilledWildcards){return position;}bool isMaskHasNoWildcards=Array.TrueForAll(wildcardsMask,x=>!x);if(isMaskHasNoWildcards){Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPattern);byte[]genuineArray=extractedData.Item1;int skippedFromStartGenuine=extractedData.Item2.Item1;int skippedFromEndGenuine=extractedData.Item2.Item2;return FindFromPosition(genuineArray,position+skippedFromStart,skippedFromStartGenuine,skippedFromEndGenuine,skippedFromEnd)-skippedFromStart;}long foundPosition=-1;byte[]buffer=new byte[bufferSize+searchPattern.Length-1];int bytesRead;stream.Position=position;bool isPatternHaveDuplicatesAtEdges=skippedFromStart>0||skippedFromEnd>0;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){int index=0;while(index<=(bytesRead-searchPattern.Length)){int foundIndex=Array.IndexOf(buffer,searchPattern[0],index);if(foundIndex==-1||foundIndex+searchPattern.Length>buffer.Length)break;bool match=true;for(int j=1;j<searchPattern.Length;j++){if(!wildcardsMask[j]&&buffer[foundIndex+j]!=searchPattern[j]){match=false;break;}}if(match){foundPosition=position+foundIndex;if(isPatternHaveDuplicatesAtEdges){if(skippedFromStart>foundPosition||foundPosition-skippedFromStart<position){match=false;index=foundIndex+1;continue;}if(skippedFromEnd>stream.Length-foundPosition){return-1;}return foundPosition-skippedFromStart;}else{return foundPosition;}}else{index=foundIndex+1;}}position+=bytesRead-searchPattern.Length+1;if(position>stream.Length-searchPattern.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return foundPosition;}public long FindFromPosition(string searchPattern,long position=0){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");if(position<0)throw new ArgumentOutOfRangeException("position should more than zero");if(position>stream.Length)throw new ArgumentOutOfRangeException("position must be within the stream body");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(searchPatternBytes,wildcardsMask);byte[]genuineArray=extractedData.Item1.Item1;bool[]genuineMask=extractedData.Item1.Item2;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;return FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,position,skippedFromStart,skippedFromEnd);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPatternBytes);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;return FindFromPosition(genuineArray,position,skippedFromStart,skippedFromEnd);}}public long FindFirst(string searchPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(searchPatternBytes,wildcardsMask);byte[]genuineArray=extractedData.Item1.Item1;bool[]genuineMask=extractedData.Item1.Item2;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;return FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,0,skippedFromStart,skippedFromEnd);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPatternBytes);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;return FindFromPosition(genuineArray,0,skippedFromStart,skippedFromEnd);}}public long FindFirst(byte[]searchPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPattern);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;return FindFromPosition(genuineArray,0,skippedFromStart,skippedFromEnd);}public long[]Find(string searchPattern,int amount){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");if(amount>stream.Length)throw new ArgumentOutOfRangeException("amount search occurrences should be less than count bytes in stream");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;return Find_WithWildcardsMask(searchPatternBytes,wildcardsMask,amount);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);return Find(searchPatternBytes,amount);}}private long[]Find_WithWildcardsMask(byte[]searchPattern,bool[]wildcardsMask,int amount){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(wildcardsMask==null)throw new ArgumentNullException("wildcardsMask argument not given");if(searchPattern.Length!=wildcardsMask.Length)throw new ArgumentException("wildcardsMask and search pattern must be same length");if(amount>stream.Length)throw new ArgumentOutOfRangeException("amount replace occurrences should be less than count bytes in stream");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));bool isMaskHasNoWildcards=Array.TrueForAll(wildcardsMask,x=>!x);if(isMaskHasNoWildcards){return Find(searchPattern,amount);}List<long>foundPositions=new List<long>();bool isMaskFilledWildcards=Array.TrueForAll(wildcardsMask,x=>x);if(isMaskFilledWildcards){long tempPosition=0;long counter=0;foundPositions.Add(tempPosition);while(tempPosition<stream.Length||counter<amount){tempPosition+=searchPattern.Length;if(tempPosition<stream.Length){foundPositions.Add(tempPosition);counter++;}else{return foundPositions.ToArray();}}return foundPositions.ToArray();}Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(searchPattern,wildcardsMask);byte[]genuineArray=extractedData.Item1.Item1;bool[]genuineMask=extractedData.Item1.Item2;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;long firstFoundPosition=FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,0,skippedFromStart,skippedFromEnd);foundPositions.Add(firstFoundPosition);if(firstFoundPosition>0||amount>1){for(int i=1;i<amount;i++){long nextFoundPosition=FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,foundPositions[foundPositions.Count-1]+searchPattern.Length,skippedFromStart,skippedFromEnd);if(nextFoundPosition>0){foundPositions.Add(nextFoundPosition);}else{break;}}}return foundPositions.ToArray();}public long[]Find(byte[]searchPattern,int amount){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(amount>stream.Length)throw new ArgumentOutOfRangeException("amount replace occurrences should be less than count bytes in stream");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPattern);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;List<long>foundPositions=new List<long>();long firstFoundPosition=FindFirst(searchPattern);foundPositions.Add(firstFoundPosition);if(firstFoundPosition>0||amount>1){for(int i=1;i<amount;i++){long nextFoundPosition=FindFromPosition(genuineArray,foundPositions[foundPositions.Count-1]+searchPattern.Length,skippedFromStart,skippedFromEnd);if(nextFoundPosition>0){foundPositions.Add(nextFoundPosition);}else{break;}}}return foundPositions.ToArray();}public long[]FindAll(byte[]searchPattern){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(searchPattern.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPattern);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;List<long>foundPositionsList=new List<long>();long foundPosition=FindFirst(searchPattern);foundPositionsList.Add(foundPosition);if(foundPosition>0){while(foundPosition<stream.Length-searchPattern.Length){foundPosition=FindFromPosition(genuineArray,foundPositionsList[foundPositionsList.Count-1]+searchPattern.Length,skippedFromStart,skippedFromEnd);if(foundPosition>0){foundPositionsList.Add(foundPosition);}else{break;}}}return foundPositionsList.ToArray();}public long[]FindAll(string searchPattern){if(string.IsNullOrEmpty(searchPattern))throw new ArgumentNullException("searchPattern argument not given");bool isSearchPatternContainWildcards=TestHexStringContainWildcards(searchPattern);if(isSearchPatternContainWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(searchPattern);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;return FindAll_WithWildcardsMask(searchPatternBytes,wildcardsMask);}else{byte[]searchPatternBytes=ConvertHexStringToByteArray(searchPattern);Tuple<byte[],Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges(searchPatternBytes);byte[]genuineArray=extractedData.Item1;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;List<long>foundPositionsList=new List<long>();long firstFoundPosition=FindFirst(searchPatternBytes);foundPositionsList.Add(firstFoundPosition);if(firstFoundPosition>0){long nextFoundPosition=firstFoundPosition;while(nextFoundPosition<stream.Length-searchPatternBytes.Length){nextFoundPosition=FindFromPosition(genuineArray,foundPositionsList[foundPositionsList.Count-1]+searchPatternBytes.Length,skippedFromStart,skippedFromEnd);if(nextFoundPosition>0){foundPositionsList.Add(nextFoundPosition);}else{break;}}}return foundPositionsList.ToArray();}}private long[]FindAll_WithWildcardsMask(byte[]searchPattern,bool[]wildcardsMask){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(wildcardsMask==null)throw new ArgumentNullException("wildcardsMask argument not given");if(searchPattern.Length!=wildcardsMask.Length)throw new ArgumentException("wildcardsMask and search pattern must be same length");if(searchPattern.Length>bufferSize)throw new ArgumentOutOfRangeException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));bool isMaskHasNoWildcards=Array.TrueForAll(wildcardsMask,x=>!x);if(isMaskHasNoWildcards){return FindAll(searchPattern);}List<long>foundPositions=new List<long>();bool isMaskFilledWildcards=Array.TrueForAll(wildcardsMask,x=>x);if(isMaskFilledWildcards){long tempPosition=0;foundPositions.Add(tempPosition);while(tempPosition<stream.Length){tempPosition+=searchPattern.Length;if(tempPosition<stream.Length){foundPositions.Add(tempPosition);}else{return foundPositions.ToArray();}}return foundPositions.ToArray();}Tuple<Tuple<byte[],bool[]>,Tuple<int,int>>extractedData=extractArrayWithoutDuplicatesAtEdges_WithWildcardsMask(searchPattern,wildcardsMask);byte[]genuineArray=extractedData.Item1.Item1;bool[]genuineMask=extractedData.Item1.Item2;int skippedFromStart=extractedData.Item2.Item1;int skippedFromEnd=extractedData.Item2.Item2;long firstFoundPosition=FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,0,skippedFromStart,skippedFromEnd);foundPositions.Add(firstFoundPosition);if(firstFoundPosition>0){long nextFoundPosition=firstFoundPosition;while(nextFoundPosition<stream.Length-searchPattern.Length){nextFoundPosition=FindFromPosition_WithWildcardsMask(genuineArray,genuineMask,foundPositions[foundPositions.Count-1]+searchPattern.Length,skippedFromStart,skippedFromEnd);if(nextFoundPosition>0){foundPositions.Add(nextFoundPosition);}else{break;}}}return foundPositions.ToArray();}public void PasteBytesSequenceAtOffset(byte[]sequence,long offset){if(sequence==null)throw new ArgumentNullException("sequence argument not given");if(offset<0)throw new ArgumentOutOfRangeException("offset should more than zero");if(offset>stream.Length)throw new ArgumentOutOfRangeException("offset must be within the stream");if(offset+sequence.Length>stream.Length)throw new ArgumentOutOfRangeException("sequence must not extend beyond the file");stream.Seek(offset,SeekOrigin.Begin);stream.Write(sequence,0,sequence.Length);}private void PasteBytesSequenceAtOffset_WithWildcardsMask(byte[]sequence,bool[]wildcardsMask,long offset){if(sequence==null)throw new ArgumentNullException("sequence argument not given");if(wildcardsMask==null)throw new ArgumentNullException("wildcardsMask argument not given");if(sequence.Length!=wildcardsMask.Length)throw new ArgumentException("wildcardsMask and sequence bytes must be same length");if(offset<0)throw new ArgumentOutOfRangeException("offset should more than zero");if(offset>stream.Length)throw new ArgumentOutOfRangeException("offset must be within the stream");if(offset+sequence.Length>stream.Length)throw new ArgumentOutOfRangeException("sequence must not extend beyond the file");stream.Seek(offset,SeekOrigin.Begin);for(int i=0;i<sequence.Length;i++){if(wildcardsMask[i]){stream.Position+=1;continue;}stream.WriteByte(sequence[i]);}}public void PasteBytesSequenceAtOffset(string sequence,long offset){if(string.IsNullOrEmpty(sequence))throw new ArgumentNullException("sequence argument not given");if(offset<0)throw new ArgumentOutOfRangeException("offset should more than zero");if(offset>stream.Length)throw new ArgumentOutOfRangeException("offset must be within the stream");bool isSequenceHaveWildcards=TestHexStringContainWildcards(sequence);;if(isSequenceHaveWildcards){Tuple<byte[],bool[]>dataPair=ConvertHexStringWithWildcardsToByteArrayAndMask(sequence);byte[]searchPatternBytes=dataPair.Item1;bool[]wildcardsMask=dataPair.Item2;PasteBytesSequenceAtOffset_WithWildcardsMask(searchPatternBytes,wildcardsMask,offset);}else{byte[]sequenceArr=ConvertHexStringToByteArray(sequence);PasteBytesSequenceAtOffset(sequenceArr,offset);}}public void Dispose(){stream.Dispose();}public long FindFromPosition_legacy(byte[]searchPattern,long position=0){if(searchPattern==null)throw new ArgumentNullException("searchPattern argument not given");if(position<0)throw new ArgumentNullException("position should more than zero");if(position>stream.Length)throw new ArgumentNullException("position must be within the stream body");if(searchPattern.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",searchPattern.Length,bufferSize));long foundPosition=-1;byte[]buffer=new byte[bufferSize+searchPattern.Length-1];int bytesRead;stream.Position=position;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){for(int i=0;i<=bytesRead-searchPattern.Length;i++){bool match=true;for(int j=0;j<searchPattern.Length;j++){if(buffer[i+j]!=searchPattern[j]){match=false;break;}}if(match){foundPosition=position+i;return foundPosition;}}position+=bytesRead-searchPattern.Length+1;if(position>stream.Length-searchPattern.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return foundPosition;}public long[]Replace_legacy(byte[]find,byte[]replace,int amount){if(amount<1)throw new ArgumentNullException("amount argument must be more than 0");if(find==null)throw new ArgumentNullException("find argument not given");if(replace==null)throw new ArgumentNullException("replace argument not given");if(find.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",find.Length,bufferSize));long position=0;List<long>foundPositions=new List<long>();byte[]buffer=new byte[bufferSize+find.Length-1];int bytesRead;stream.Position=0;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){for(int i=0;i<=bytesRead-find.Length;i++){bool match=true;for(int j=0;j<find.Length;j++){if(buffer[i+j]!=find[j]){match=false;break;}}if(match){stream.Seek(position+i,SeekOrigin.Begin);stream.Write(replace,0,replace.Length);if(foundPositions.Count<amount){foundPositions.Add(position+i);}else{return foundPositions.ToArray();}}}position+=bytesRead-find.Length+1;if(position>stream.Length-find.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return foundPositions.ToArray();}public long[]ReplaceAll_legacy(byte[]find,byte[]replace){if(find==null)throw new ArgumentNullException("find argument not given");if(replace==null)throw new ArgumentNullException("replace argument not given");if(find.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",find.Length,bufferSize));long position=0;List<long>foundPositions=new List<long>();byte[]buffer=new byte[bufferSize+find.Length-1];int bytesRead;stream.Position=0;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){for(int i=0;i<=bytesRead-find.Length;i++){bool match=true;for(int j=0;j<find.Length;j++){if(buffer[i+j]!=find[j]){match=false;break;}}if(match){stream.Seek(position+i,SeekOrigin.Begin);stream.Write(replace,0,replace.Length);foundPositions.Add(position+i);}}position+=bytesRead-find.Length+1;if(position>stream.Length-find.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return foundPositions.ToArray();}public long ReplaceOnce_legacy(byte[]find,byte[]replace){if(find==null)throw new ArgumentNullException("find argument not given");if(replace==null)throw new ArgumentNullException("replace argument not given");if(find.Length>bufferSize)throw new ArgumentException(string.Format("Find size {0} is too large for buffer size {1}",find.Length,bufferSize));long position=0;long foundPosition=-1;byte[]buffer=new byte[bufferSize+find.Length-1];int bytesRead;stream.Position=0;while((bytesRead=stream.Read(buffer,0,buffer.Length))>0){for(int i=0;i<=bytesRead-find.Length;i++){bool match=true;for(int j=0;j<find.Length;j++){if(buffer[i+j]!=find[j]){match=false;break;}}if(match){stream.Seek(position+i,SeekOrigin.Begin);stream.Write(replace,0,replace.Length);if(foundPosition==-1){foundPosition=position+i;return foundPosition;}}}position+=bytesRead-find.Length+1;if(position>stream.Length-find.Length){break;}stream.Seek(position,SeekOrigin.Begin);}return foundPosition;}}}
"@


# =====
# FUNCTIONS
# =====


<#
.SYNOPSIS
Function for check if for re-write transferred file need admins privileges

.DESCRIPTION
First, we check the presence of the "read-only" attribute and try to remove this attribute.
If it is cleaned without errors, then admin rights are not needed (or they have already been issued to this script).
If there is no "read-only" attribute, then we check the possibility to change the file.
#>
function Test-ReadOnlyAndWriteAccess {
    [OutputType([bool[]])]
    param (
        [string]$targetPath
    )
    
    $fileAttributes = Get-Item -Path "$targetPath" -Force | Select-Object -ExpandProperty Attributes
    [bool]$isReadOnly = $false
    [bool]$needRunAs = $false

    if ($fileAttributes -band [System.IO.FileAttributes]::ReadOnly) {
        try {
            Set-ItemProperty -Path "$targetPath" -Name Attributes -Value ($fileAttributes -bxor [System.IO.FileAttributes]::ReadOnly)
            $isReadOnly = $true
            Set-ItemProperty -Path "$targetPath" -Name Attributes -Value ($fileAttributes -bor [System.IO.FileAttributes]::ReadOnly)
            $needRunAs = $false
        }
        catch {
            $isReadOnly = $true
            $needRunAs = $true
        }
    }
    else {
        $isReadOnly = $false

        try {
            $stream = [System.IO.File]::Open($targetPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write)
            $stream.Close()
            $needRunAs = $false
        }
        catch {
            $needRunAs = $true
        }
    }

    return $isReadOnly, $needRunAs
}


<#
.DESCRIPTION
Function detect if current script run as administrator
and return bool info about it
#>
function DoWeHaveAdministratorPrivileges {
    [OutputType([bool])]
    param ()

    if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        return $false
    }
    else {
        return $true
    }
}


<#
.DESCRIPTION
A set of patterns can be passed not as an array, but as 1 line
   this usually happens if this script is called on behalf of the administrator from another Powershell script
In this case, this string becomes the first and only element of the pattern array
We need to divide the string into an array of patterns (extract all patterns from 1 string)
#>
function ExtractPatterns {
    [OutputType([string[]])]
    param (
        [Parameter(Mandatory)]
        [string]$patternsString
    )

    return $patternsString.Replace('"', "").Replace("'", "").Split(',')
}


<#
.SYNOPSIS
Function for clean hex string and separate search and replace patterns

.DESCRIPTION
The pattern array contains strings. Each string is a set of bytes to search
    and replace in a non-strict format.
Non-strict means that the presence or absence of spaces between byte values
    is allowed, as well as the presence or absence of "\x" characters denoting 16-bit data.
The value separator for search and replace can be one of the characters: \, /, |

Then all this is divided into 2 arrays - an array with search patterns
    and an array with replacement patterns and return both arrays
#>
function Separate-Patterns {
    [OutputType([string[]])]
    param (
        [Parameter(Mandatory)]
        [string[]]$patternsArray
    )
    
    [System.Collections.Generic.List[string]]$searchPatterns = New-Object System.Collections.Generic.List[string]
    [System.Collections.Generic.List[string]]$replacePatterns = New-Object System.Collections.Generic.List[string]

    # Separate pattern-string on search and replace strings
    foreach ($pattern in $patternsArray) {
        # Clean and split string with search and replace hex patterns
        [string[]]$temp = $pattern.Clone().Replace(" ", "").Replace("\", "/").Replace("|", "/").ToUpper().Split("/")

        if (-not ($temp.Count -eq 2) -or $temp[1].Length -eq 0) {
            throw "Search pattern $pattern not have replace pattern"
        }

        [void]($searchPatterns.Add($temp[0]))
        [void]($replacePatterns.Add($temp[1]))
    }

    return $searchPatterns.ToArray(), $replacePatterns.ToArray()
}


<#
.DESCRIPTION
Getting the path to the file
and return absolute path for temp file in same folder
#>
function Get-UniqTempFileName {
    [OutputType([string])]
    param (
        [Parameter(Mandatory)]
        [string]$targetPath
    )
    
    [string]$tempFilePath = "$targetPath.temp"
    while (-not (Test-Path $tempFilePath)) {
        if (-not (Test-Path $tempFilePath)) {
            break
        }

        $tempFilePath += (Get-Random -Maximum 10)
    }
    
    return $tempFilePath
}


<#
.DESCRIPTION
Check attribute and permission for target file and handle search + replace patterns

.OUTPUTS
Array with numbers of found occurrences for each search pattern
#>
function Apply-HexPatternInBinaryFile {
    [OutputType([int[]])]
    param (
        [Parameter(Mandatory)]
        [string]$targetPath,
        [Parameter(Mandatory)]
        [string[]]$patternsArray,
        [Parameter(Mandatory)]
        [bool]$needMakeBackup
    )

    [string]$backupAbsoluteName = "$targetPath.bak"
    [string]$backupTempAbsoluteName = Get-UniqTempFileName -targetPath $targetPath

    $isReadOnly, $needRunAS = Test-ReadOnlyAndWriteAccess $targetPath

    KillExeTasks $targetPath

    if ($needRunAS -and !(DoWeHaveAdministratorPrivileges)) {
        # relaunch current script in separate process with Admins privileges
        Start-Process -Verb RunAs $PSHost ("-ExecutionPolicy Bypass -File `"$PSCommandPath`" $PSBoundParametersStringGlobal")
        break
    }

    $fileAcl = Get-Acl "$targetPath"
    $fileAttributes = Get-Item -Path "$targetPath" -Force | Select-Object -ExpandProperty Attributes

    try {
        if ($isReadOnly) {
            Set-ItemProperty -Path "$targetPath" -Name Attributes -Value ($fileAttributes -bxor [System.IO.FileAttributes]::ReadOnly)
        }
    
        if ($needMakeBackup) {
            # Make temp backup file
            Copy-Item -Path "$targetPath" -Destination "$backupTempAbsoluteName" -Force
        }

        [int[]]$numbersFoundOccurrences = SearchAndReplace-HexPatternInBinaryFile -targetPath $targetPath -patternsArray $patternsArray
    }
    catch {
        Remove-Item -Path "$backupTempAbsoluteName" -Force
        Remove-Item -Path "$backupAbsoluteName" -Force

        Write-Error $_.Exception.Message
        exit 1
    }
    finally {
        # restore file permissions
        $fileAcl | Set-Acl "$targetPath"

        # restore attribute "Read Only" if it was
        if ($isReadOnly) {
            Set-ItemProperty -Path "$targetPath" -Name Attributes -Value ($fileAttributes -bor [System.IO.FileAttributes]::ReadOnly)
        }
    }



    # if target file patched we need rename temp backuped file to "true" backuped file
    # and restore attributes and permissions

    if ($needMakeBackup) {
        if (Test-Path $backupAbsoluteName) {
            try {
                $fileAttributesForBackup = Get-Item -Path "$backupAbsoluteName" -Force | Select-Object -ExpandProperty Attributes
                
                # remove "Read Only" attribute from exist backuped file
                Set-ItemProperty -Path "$backupAbsoluteName" -Name Attributes -Value ($fileAttributesForBackup -bxor [System.IO.FileAttributes]::ReadOnly)
                Remove-Item -Path "$backupAbsoluteName" -Force
            }
            catch {
                # IMPORTANT !!!
                # Do not formate this command and not re-write it
                # it need for add multiline string to Start-Process command
                $command = @"
$fileAttributesForBackup = Get-Item -Path '$backupAbsoluteName' -Force | Select-Object -ExpandProperty Attributes
Set-ItemProperty -Path '$backupAbsoluteName' -Name Attributes -Value ('$fileAttributesForBackup' -bxor [System.IO.FileAttributes]::ReadOnly)
Remove-Item -Path '$backupAbsoluteName' -Force
"@

                # Start-Process $PSHost -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -Command `"$command`""
                $processId = Start-Process $PSHost -Verb RunAs -PassThru -Wait -ArgumentList "-ExecutionPolicy Bypass -WindowStyle Hidden -NoProfile -Command `"$command`""

                if ($processId.ExitCode -gt 0) {
                    throw "Something happened wrong when try remove previously backuped file"
                }
            }
        }

        # with copying it wil be replaced
        Rename-Item -Path "$backupTempAbsoluteName" -NewName "$backupAbsoluteName" -Force

        # restore attribute "Read Only" if it was on original file
        if ($isReadOnly) {
            Set-ItemProperty -Path "$backupAbsoluteName" -Name Attributes -Value ($fileAttributes -bor [System.IO.FileAttributes]::ReadOnly)
        }

        # restore file permissions
        $fileAcl | Set-Acl "$backupAbsoluteName"
    }

    return $numbersFoundOccurrences
}


<#
.SYNOPSIS
Return index first bytes not matched with index wildcard
#>
function Get-IndexFirstTrueByte {
    [OutputType([int])]
    param (
        [Parameter(Mandatory)]
        [System.Collections.Generic.List[byte]]$hexBytes,
        [Parameter(Mandatory)]
        [System.Collections.Generic.List[int]]$wildcardsIndexes
    )

    if ($wildcardsIndexes.Count -eq 0) {
        return 0
    }

    for ($i = 0; $i -lt $hexBytes.Count; $i++) {
        if ($wildcardsIndexes.Contains($i)) {
            continue
        }
        else {
            return $i
        }
    }
}


<#
.SYNOPSIS
Function to search and replace hex patterns in a binary file

.DESCRIPTION
Loop in given patterns array and search each search-pattern and replace
    all found replace-patterns in given file
    and return indexes found patterns from given patterns array

.OUTPUTS
Array with numbers of found occurrences for each search pattern
#>
function SearchAndReplace-HexPatternInBinaryFile {
    [OutputType([int[]])]
    param (
        [Parameter(Mandatory)]
        [string]$targetPath,
        [Parameter(Mandatory)]
        [string[]]$patternsArray
    )

    [string[]]$searchPatterns, [string[]]$replacePatterns = Separate-Patterns $patternsArray

    try {
        $stream = [System.IO.File]::Open($targetPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite)
    }
    catch {
        [void]($stream.Close())
        
        # If error when read file it looks like we have not rights
        # and we need request admin privileges - re-launch script with admin privileges
        Start-Process -Verb RunAs $PSHost ("-ExecutionPolicy Bypass -NoExit -File `"$PSCommandPath`" $PSBoundParametersStringGlobal")
        break
    }

    # if any method from C# code exist - C# already imported in the script and not need compile and import it again
    if (-not ("HexHandler.BytesReplacer" -as [Type])) {
        Add-Type -TypeDefinition $hexHandlerCodeMinified -Language CSharp
    }

    [System.Collections.Generic.List[int]]$numbersFoundOccurrences = New-Object System.Collections.Generic.List[int]
    $BytesHandler = [HexHandler.BytesHandler]::new($stream)

    try {
        for ($i = 0; $i -lt $searchPatterns.Count; $i++) {
            [long[]]$positionsTemp = $BytesHandler.OverwriteBytesAtAllPatternPositions($searchPatterns[$i], $replacePatterns[$i])
            # [long[]]$positionsTemp = $BytesHandler.FindAll($searchPatterns[$i])


            if (($positionsTemp.Count -eq 1) -and ($positionsTemp[0] -eq -1)) {
                [void]($numbersFoundOccurrences.Add(0))
            }
            else {
                [void]($numbersFoundOccurrences.Add($positionsTemp.Count))
            }
        }
    }
    finally {
        $stream.Close()
    }

    return $numbersFoundOccurrences.ToArray()
}


<#
.SYNOPSIS
Kill the process that occupies the target file
#>
function KillExeTasks {
    param (
        [Parameter(Mandatory)]
        [string]$targetPath
    )

    # TODO:
    # Also need good way for kill process blocked access to file if file not launched

    if (($targetPath.Length -eq 0) -or (-not (Test-Path $targetPath))) {
        return
    }
    
    $targetName = [System.IO.Path]::GetFileNameWithoutExtension($targetPath)

    $process = Get-Process | ForEach-Object {
        if ($_.Path -eq $targetPath) {
            return $_.Path -eq $targetPath
        }
    }

    if ($process) {
        try {
            Stop-Process -Name $targetName -Force
        }
        catch {
            if (-not (DoWeHaveAdministratorPrivileges)) {
                $processId = Start-Process $PSHost -Verb RunAs -PassThru -Wait -ArgumentList "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -Command `"Stop-Process -Name '$targetName' -Force`""

                if ($processId.ExitCode -gt 0) {
                    throw "Something happened wrong when try kill process with target file"
                }
            }
    
        }
    }
}

function Test-AllZero([int[]] $array) {
    for ($i = 0; $i -lt $array.Count; $i++) {
        if ($array[$i] -ne 0) { return $false }
    }
    return $true
}

function Test-AllNonZero([int[]] $array) {
    for ($i = 0; $i -lt $array.Count; $i++) {
        if ($array[$i] -eq 0) { return $false }
    }
    return $true
}

<#
.SYNOPSIS
Show info about found+replaced or not found patterns
#>
function ShowInfoAboutReplacedPatterns {
    param (
        [Parameter(Mandatory)]
        [string[]]$patternsArray,
        [Parameter(Mandatory)]
        [int[]]$numbersFoundOccurrences,
        [bool]$needMoreInfo = $false
    )
    
    [bool]$isAllPatternsNotFound = Test-AllZero $numbersFoundOccurrences
    [bool]$isAllPatternsFound = Test-AllNonZero $numbersFoundOccurrences

    [string]$notFoundPatterns = ''

    if ($isAllPatternsNotFound) {
        Write-Host "No patterns was found in $filePathFull"
    }
    elseif ($isAllPatternsFound) {
        Write-Host "All hex patterns found and replaced successfully in $filePathFull"
    }
    else {
        if ($needMoreInfo) {
            Write-Host "Not all patterns was found!"
            Write-Host ""
            Write-Host "Here details - <Pattern>: <occurrences>"
            
            for ($i = 0; $i -lt $numbersFoundOccurrences.Count; $i++) {
                Write-Host "$($patternsArray[$i]) : $($numbersFoundOccurrences[$i])"
            }
            Write-Host ""
            Write-Host "In file `"$filePathFull`""
        }
        else {
            for ($i = 0; $i -lt $numbersFoundOccurrences.Count; $i++) {
                if ($numbersFoundOccurrences[$i] -eq 0) {
                    $notFoundPatterns += ' ' + $patternsArray[$i]
                }
    
                Write-Host "Hex patterns" $notFoundPatterns.Trim() "- not found, but other given patterns found and replaced successfully in $filePathFull" 
            }
        }
    }
}



# =====
# MAIN
# =====

if (-not $skipStopwatch) {
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $watch.Start() # launch timer
}

Write-Host "Start handle patterns..."
Write-Host ""

[string[]]$patternsExtracted = @()
if ($patterns.Count -eq 1) {
    # Maybe all patterns written in 1 string if first array item and we need handle it
    $patternsExtracted = ExtractPatterns $patterns[0]
}
else {
    $patternsExtracted = $patterns
}

[int[]]$numbersFoundOccurrences = Apply-HexPatternInBinaryFile -targetPath $filePathFull -patterns $patternsExtracted -needMakeBackup $makeBackup

ShowInfoAboutReplacedPatterns $patternsExtracted $numbersFoundOccurrences $showMoreInfo

if (-not $skipStopwatch) {
    $watch.Stop()
    Write-Host "Script execution time is" $watch.Elapsed # time of execution code
}
Write-Host ""

# Pause before exit like in CMD
Write-Host -NoNewLine "Press any key to continue...`r`n";
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
